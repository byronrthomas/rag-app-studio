from datetime import datetime
import json
import os
import shutil
import sys
from dotenv import dotenv_values
from flask import Flask, jsonify, render_template, request, redirect
from flask_cors import CORS
from rag_studio.model_builder import ModelBuilder
from rag_studio.ragstore import RagStore
from rag_studio.hf_repo_storage import (
    download_from_repo,
    init_repo,
    get_last_commit,
    upload_folder,
)
import logging
from llama_index.core import (
    Settings,
)
import gc

logger = logging.getLogger(__name__)

DEFAULT_LLM_MODEL = "mistralai/Mistral-7B-Instruct-v0.1"
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"


def apply_defaults(config_in, from_dot_env=None):
    """Apply the default config values."""
    # Allow from_dot_env to override the config
    if from_dot_env:
        config = {**config_in, **from_dot_env}
    else:
        config = config_in
    logger.info("Original config: %s", config_in)
    logger.info("Dotenv config: %s", from_dot_env)
    logger.info("Merged config: %s", config)
    rag_storage_path = config.get("RAG_STORAGE_PATH", "/tmp/rag_store/rag_storage")

    return {
        "models_download_folder": config.get(
            "MODELS_DOWNLOAD_FOLDER", "/tmp/rag_store/models"
        ),
        "rag_storage_path": rag_storage_path,
        "doc_storage_path": config.get(
            "DOC_STORAGE_PATH", "/tmp/rag_store/doc_storage"
        ),
        # NOTE: convenience to look it up - must be within the rag storage path
        "model_settings_path": f"{rag_storage_path}/model_settings.json",
        "repo_name": config.get("REPO_NAME", None),
    }


def initial_engine(model_builder, settings):
    """Initialise the inference engine using the model builder."""
    engine = {}
    engine["embed_model"] = model_builder.make_embedding_model(DEFAULT_EMBEDDING_MODEL)
    engine["llm"] = model_builder.make_llm(settings["model"])
    return engine


def fetch_full_repo(config, repo_name):
    """Fetch the existing files from the repo."""
    logger.info("Fetching repo %s", repo_name)
    download_from_repo(repo_name, config["rag_storage_path"])
    # Return the JSON settings
    with open(config["model_settings_path"], "r", encoding="UTF-8") as f:
        return json.load(f)


def write_settings(config, settings):
    """Write the settings to the settings file."""
    with open(config["model_settings_path"], "w", encoding="UTF-8") as f:
        json.dump(settings, f)


def push_to_repo(repo_name, config):
    upload_folder(repo_name, config["rag_storage_path"])


def push_initial_model_settings(config, repo_name):
    """Push the initial model settings to the repo."""
    logger.info("Pushing initial model settings to repo %s", repo_name)
    storage_path = config["rag_storage_path"]
    if os.path.exists(storage_path):
        logger.info("Clearing out storage path %s", storage_path)
        # Remove the directory tree at storage_path, even if the dir is not empty
        shutil.rmtree(storage_path)
    os.makedirs(storage_path)
    write_settings(config, {"model": DEFAULT_LLM_MODEL})
    push_to_repo(repo_name, config)


def init_settings(config, repo_name):
    """Init model settings, either downloading from existing repo, or creating repo
    and pushing default settings to it if it doesn't exist."""
    if not repo_name:
        logger.info("No repo name set, creating repo")
        repo_name = init_repo(repo_name)
        # Push the initial model settings to the repo
        config["repo_name"] = repo_name
        push_initial_model_settings(config, repo_name)

    return fetch_full_repo(config, repo_name)


def create_app(config=None, model_builder=None):
    """Create the main Flask app with the given config."""
    config = apply_defaults(config or {}, dotenv_values(".env"))
    app = Flask(__name__)
    CORS(app)

    # Capture the current time
    startTime = datetime.now()

    settings = init_settings(config, config["repo_name"])
    logger.info("Model settings on server initialisation: %s", settings)
    if not model_builder:
        model_builder = ModelBuilder(config["models_download_folder"])
    _engine = initial_engine(model_builder, settings)

    # Need to wire in the RAG storage initialisation here, based on path
    # from config object
    rag_storage_path = config["rag_storage_path"]
    logger.info("RAG storage path: %s", rag_storage_path)
    rag_storage = RagStore(rag_storage_path, embed_model=_engine["embed_model"])
    doc_storage_path = config["doc_storage_path"]
    logger.info("Document storage path: %s", doc_storage_path)
    if not os.path.exists(doc_storage_path):
        os.makedirs(doc_storage_path)

    # logger.info("Initialising repo at %s", config["repo_name"])
    # repo_name = init_repo(config["repo_name"])
    repo_name = config["repo_name"]
    if not repo_name:
        logger.error("Repo name should have been set already - dumb programmer error!")
        sys.exit(1)

    @app.route("/healthcheck")
    def healthcheck_api():
        """Healthcheck API to check if the API is running."""
        return {
            "message": "API is running!",
            "start_time": startTime.strftime("%Y-%m-%d %H:%M:%S"),
        }

    @app.route("/repo_name")
    def get_repo_name():
        return {"repo_name": repo_name}

    def checkpoint_docs():
        rag_storage.write_to_storage()
        push_to_repo(repo_name, config)

    def handle_file_upload():
        if "file" not in request.files:
            return "No file part in the request"
        file = request.files["file"]
        if file.filename == "":
            return "No file selected for uploading"
        if file:
            write_path = f"{doc_storage_path}/{file.filename}"
            logger.info("Uploading file %s to %s", file.filename, write_path)
            file.save(write_path)
            rag_storage.add_document(write_path)
            checkpoint_docs()

    @app.route("/upload", methods=["POST"])
    def upload_file_api():
        err_msg = handle_file_upload()
        if err_msg:
            return {"message": err_msg}, 400
        return {"message": "File uploaded successfully"}

    @app.route("/upload-view", methods=["POST"])
    def upload_file_view():
        err_msg = handle_file_upload()
        if err_msg:
            return err_msg, 400

        return redirect("/")

    @app.route("/files")
    def list_files_api():
        return {"files": rag_storage.list_files()}

    @app.route("/trycompletion", methods=["POST"])
    def try_completion_api():
        prompt = request.json["prompt"]
        response = complete_prompt(prompt)
        return {"completion": response.response}

    def complete_prompt(prompt):
        response = rag_storage.make_query_engine(llm=_engine["llm"]).query(prompt)
        logger.debug("Response from query engine: %s", response)
        return response

    @app.route("/inference-container-details", methods=["POST"])
    def inference_container_details_api():
        return {"message": "Inference container details"}

    @app.route(
        "/last-checkpoint",
    )
    def last_checkpoint_api():
        last_commit = get_last_commit(repo_name)
        if last_commit is None:
            return {"latest_change_time": None}
        return {"latest_change_time": last_commit.created_at}

    @app.post("/model")
    def update_model():
        del _engine["llm"]
        gc.collect()
        if request.json.get("clear_space") == True:
            model_builder.clear_vllm_models_folder()

        logger.info("Loading the model %s", request.json["model_name"])
        settings["model"] = request.json["model_name"]
        write_settings(config, settings)
        push_to_repo(repo_name, config)

        _engine["llm"] = model_builder.make_llm(request.json["model_name"])
        return {"message": "Model updated"}

    @app.route("/model-name")
    def get_model_name():
        return {"model_name": settings["model"]}

    @app.post("/complete")
    def try_completion_view():
        prompt = request.form["prompt"]
        response = complete_prompt(prompt)
        return f"<div>{response}</div>"

    @app.route("/")
    def home():
        content = {
            "llm_model": settings["model"],
            "repo_name": repo_name,
            "files": list_files_api()["files"],
            "embed_model": DEFAULT_EMBEDDING_MODEL,
            "completion": "",
            "last_checkpoint": last_checkpoint_api()["latest_change_time"],
        }
        return render_template("main.html", content=content)

    return app
