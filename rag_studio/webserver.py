from datetime import datetime
import os
import sys
from dotenv import dotenv_values
from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
from rag_studio.model_builder import ModelBuilder
from rag_studio.ragstore import RagStore
from rag_studio.hf_repo_storage import init_repo, get_last_commit, upload_folder
import logging
from llama_index.core import (
    Settings,
)
import gc

logger = logging.getLogger(__name__)

DEFAULT_LLM_MODEL = "mistralai/Mistral-7B-Instruct-v0.1"
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"


def apply_defaults(config):
    """Apply the default config values."""
    rag_storage_path = config.get("RAG_STORAGE_PATH", "/tmp/rag_store/rag_storage")

    return {
        "models_download_folder": config.get(
            "MODELS_DOWNLOAD_FOLDER", "/tmp/rag_store/models"
        ),
        "rag_storage_path": rag_storage_path,
        "doc_storage_path": config.get(
            "DOC_STORAGE_PATH", "/tmp/rag_store/doc_storage"
        ),
        "model_settings_path": config.get(
            "MODEL_SETTINGS_PATH", f"{rag_storage_path}/model_settings.json"
        ),
        "repo_name": config.get("REPO_NAME", None),
    }


def initial_engine(model_builder):
    """Initialise the inference engine using the model builder."""
    engine = {}
    engine["embed_model"] = model_builder.make_embedding_model(DEFAULT_EMBEDDING_MODEL)
    engine["llm"] = model_builder.make_llm(DEFAULT_LLM_MODEL)
    return engine


def create_app(config=None, model_builder=None):
    """Create the main Flask app with the given config."""
    config = apply_defaults(config or dotenv_values(".env"))
    app = Flask(__name__)
    CORS(app)

    # Capture the current time
    startTime = datetime.now()

    if not model_builder:
        model_builder = ModelBuilder(config["models_download_folder"])
    _engine = initial_engine(model_builder)

    # Need to wire in the RAG storage initialisation here, based on path
    # from config object
    rag_storage_path = config["rag_storage_path"]
    logger.info("RAG storage path: %s", rag_storage_path)
    rag_storage = RagStore(rag_storage_path, embed_model=_engine["embed_model"])
    doc_storage_path = config["doc_storage_path"]
    logger.info("Document storage path: %s", doc_storage_path)
    if not os.path.exists(doc_storage_path):
        os.makedirs(doc_storage_path)

    logger.info("Initialising repo at %s", config["repo_name"])
    repo_name = init_repo(config["repo_name"])

    @app.route("/healthcheck")
    def healthcheck_api():
        """Healthcheck API to check if the API is running."""
        return jsonify(
            {
                "message": "API is running!",
                "start_time": startTime.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    @app.route("/repo_name")
    def get_repo_name():
        return jsonify({"repo_name": repo_name})

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
        response = rag_storage.make_query_engine(llm=_engine["llm"]).query(
            request.json["prompt"]
        )
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

    @app.post("/model")
    def update_model():
        del _engine["llm"]
        gc.collect()

        logger.info("Loading the model %s", request.json["model_name"])
        _engine["llm"] = model_builder.make_llm(request.json["model_name"])
        return jsonify({"message": "Model updated"})

    @app.route("/model-name")
    def get_model_name():
        return jsonify({"model_name": DEFAULT_LLM_MODEL})

    return app
