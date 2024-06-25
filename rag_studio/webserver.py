from datetime import datetime
import os
import sys
from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
from rag_studio.ragstore import RagStore
from rag_studio.hf_repo_storage import init_repo, get_last_commit, upload_folder
import logging
from llama_index.core import (
    Settings,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.vllm import Vllm

logger = logging.getLogger(__name__)


def inference_engine(config={}):
    """Initialise the inference engine with the given config."""
    models_base_dir = config.get("models_download_folder", "/workspace/models")
    # bge-base embedding model
    Settings.embed_model = HuggingFaceEmbedding(
        model_name="BAAI/bge-large-en-v1.5",
        cache_folder=f"{models_base_dir}/.hf-cache",
    )
    # VLLM model
    Settings.llm = Vllm(
        model="mistralai/Mistral-7B-Instruct-v0.1",
        download_dir=f"{models_base_dir}/vllm-via-llama-models",
        vllm_kwargs={"max_model_len": 30000},
    )
    # Just return a dummy object - to show that we have configured the engine
    return {"configured": True}


def create_app(config=None, _engine=None):
    """Create the main Flask app with the given config."""
    config = config or {}
    app = Flask(__name__)
    CORS(app)

    # Capture the current time
    startTime = datetime.now()

    _engine = _engine or inference_engine(config)

    # Need to wire in the RAG storage initialisation here, based on path
    # from config object
    rag_storage_path = config.get("rag_storage_path", "/workspace/rag_storage")
    logger.info("RAG storage path: %s", rag_storage_path)
    rag_storage = RagStore(rag_storage_path)
    doc_storage_path = config.get("doc_storage_path", "/workspace/doc_storage")
    logger.info("Document storage path: %s", doc_storage_path)
    if not os.path.exists(doc_storage_path):
        os.makedirs(doc_storage_path)

    repo_name = init_repo(config.get("repo_name"))

    @app.route("/healthcheck")
    def healthcheck_api():
        """Healthcheck API to check if the API is running."""
        return jsonify(
            {
                "message": "API is running!",
                "start_time": startTime.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    @app.route("/upload", methods=["POST"])
    def upload_file_api():
        if "file" not in request.files:
            return jsonify({"message": "No file part in the request"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"message": "No file selected for uploading"}), 400
        if file:
            write_path = f"{doc_storage_path}/{file.filename}"
            logger.info("Uploading file %s to %s", file.filename, write_path)
            file.save(write_path)
            rag_storage.add_document(write_path)
            return jsonify({"message": "File uploaded successfully"}), 200

    @app.route("/files")
    def list_files_api():
        return jsonify({"files": rag_storage.list_files()})

    @app.route("/trycompletion", methods=["POST"])
    def try_completion_api():
        response = rag_storage.make_query_engine().query(request.json["prompt"])
        logger.debug("Response from query engine: %s", response)
        return jsonify({"completion": response.response})

    @app.route("/checkpoint", methods=["POST"])
    def checkpoint_api():
        rag_storage.write_to_storage()
        upload_folder(repo_name, rag_storage.storage_path)
        return jsonify({"message": "Checkpoint OK"})

    @app.route("/inference-container-details", methods=["POST"])
    def inference_container_details_api():
        return jsonify({"message": "Inference container details"})

    @app.route(
        "/last-checkpoint",
    )
    def last_checkpoint_api():
        last_commit = get_last_commit(repo_name)
        if last_commit is None:
            return jsonify({"latest_change_time": None})
        return jsonify({"latest_change_time": last_commit.created_at})

    return app
