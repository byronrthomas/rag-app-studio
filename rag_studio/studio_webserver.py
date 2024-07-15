from datetime import datetime
import json
import os
import shutil
import sys
from dotenv import dotenv_values
from flask import Flask, render_template, request, redirect
from flask_cors import CORS
import logging

from llama_index.core.base.llms.types import ChatMessage
import gc


from rag_studio import LOG_FILE_FOLDER
from rag_studio.evaluation.retrieval import evaluate_on_auto_dataset
from rag_studio.inference.repo_handling import infer_prefs_repo_id
from rag_studio.log_files import tail_logs
from rag_studio.model_builder import ModelBuilder
from rag_studio.model_settings import (
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_LLM_MODEL,
    app_name_from_settings,
    chat_prompts_from_settings,
    query_prompts_from_settings,
    read_settings,
)
from rag_studio.ragstore import RagStore
from rag_studio.hf_repo_storage import (
    create_repo,
    download_file,
    download_from_repo,
    init_repo,
    get_last_commit,
    repo_exists,
    upload_folder,
)

logger = logging.getLogger(__name__)


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
        "prefs_repo_dir": config.get("PREFS_REPO_DIR", "/tmp/rag_store/prefs_repo"),
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
    settings_path = config["model_settings_path"]
    return read_settings(settings_path)


def write_settings(config, settings):
    """Write the settings to the settings file."""
    with open(config["model_settings_path"], "w", encoding="UTF-8") as f:
        json.dump(settings, f)


def mark_repo_as_active(config):
    prefs = fetch_preferences(config["prefs_repo_dir"], config["prefs_repo_name"])
    prefs["active_repo_id"] = config["repo_name"]
    with open(
        f"{config['prefs_repo_dir']}/preferences.json", "w", encoding="UTF-8"
    ) as f:
        json.dump(prefs, f)
    upload_folder(config["prefs_repo_name"], config["prefs_repo_dir"])


def push_to_repo(config):
    upload_folder(config["repo_name"], config["rag_storage_path"])
    mark_repo_as_active(config)


def push_settings_update(config, settings):
    write_settings(config, settings)
    push_to_repo(config)


def push_initial_model_settings(config, repo_name):
    """Push the initial model settings to the repo."""
    logger.info("Pushing initial model settings to repo %s", repo_name)
    storage_path = config["rag_storage_path"]
    if os.path.exists(storage_path):
        logger.info("Clearing out storage path %s", storage_path)
        # Remove the directory tree at storage_path, even if the dir is not empty
        shutil.rmtree(storage_path)
    os.makedirs(storage_path)
    push_settings_update(config, {"model": DEFAULT_LLM_MODEL})


def init_settings(config, repo_name):
    """Init model settings, either downloading from existing repo, or creating repo
    and pushing default settings to it if it doesn't exist."""
    if not repo_name:
        logger.info("No repo name set, creating repo")
        repo_name = init_repo(repo_name)
        # Push the initial model settings to the repo
        config["repo_name"] = repo_name
        push_initial_model_settings(config, repo_name)

    config["repo_name"] = repo_name
    return fetch_full_repo(config, repo_name)


def response_to_transport(response):
    return {
        "completion": response.response,
        "contexts": [
            {
                "context": sn.text,
                "score": sn.score,
                "filename": sn.metadata.get("file_name"),
            }
            for sn in response.source_nodes
        ],
    }


def ensure_prefs_repo_exists(prefs_repo_dir):
    prefs_repo_id = infer_prefs_repo_id()
    if not repo_exists(prefs_repo_id):
        logger.info("Creating preferences repo %s", prefs_repo_id)
        create_repo(prefs_repo_id)
        if not os.path.exists(prefs_repo_dir):
            os.makedirs(prefs_repo_dir)
        logger.info("Pushing initial preferences to repo %s", prefs_repo_id)
        with open(f"{prefs_repo_dir}/preferences.json", "w", encoding="UTF-8") as f:
            f.write("{}")
        upload_folder(prefs_repo_id, prefs_repo_dir)
    return prefs_repo_id


def fetch_preferences(prefs_repo_dir, prefs_repo_id):
    download_file(prefs_repo_id, "preferences.json", prefs_repo_dir)
    with open(f"{prefs_repo_dir}/preferences.json", "r", encoding="UTF-8") as f:
        prefs = json.load(f)
    return prefs


def requested_storage_repo(config):
    """Returns the storage repo ID either set in environment
    or fetched from the preferences repo. If neither is set,
    returns None, allowing later code to set up a new storage repo."""
    if os.environ.get("CREATE_NEW_RAG_APP"):
        if os.environ.get("RAG_REPO_ID"):
            logger.error(
                "Cannot create new app and provide repo ID at the same time - drop RAG_REPO_ID if you want a new app"
            )
            raise ValueError(
                "Cannot set both RAG_REPO_ID and CREATE_NEW_RAG_APP - drop RAG_REPO_ID if you want a fresh app"
            )
        return None

    if os.environ.get("RAG_REPO_ID"):
        return os.environ["RAG_REPO_ID"]

    prefs = fetch_preferences(config["prefs_repo_dir"], config["prefs_repo_name"])
    logger.info("Loaded preferences %s", prefs)
    return prefs.get("active_repo_id")


def retrieval_eval_result_to_transport(ragstore, re):
    return {
        "query": re.query,
        "retrieved_texts": re.retrieved_texts,
        "expected_texts": [
            ragstore.get_node_text(node_id) for node_id in re.expected_ids
        ],
        "metrics": re.metric_vals_dict,
    }


def create_app(config=None, model_builder=None):
    """Create the main Flask app with the given config."""
    config = apply_defaults(config or {}, dotenv_values(".env"))
    app = Flask(__name__)
    CORS(app)

    # Capture the current time
    startTime = datetime.now()

    prefs_repo_id = ensure_prefs_repo_exists(config["prefs_repo_dir"])
    config["prefs_repo_name"] = prefs_repo_id
    logger.info("Preferences repo ID: %s", config["prefs_repo_name"])

    settings = init_settings(config, requested_storage_repo(config))
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
    if not config["repo_name"]:
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
        return {"repo_name": config["repo_name"]}

    def checkpoint_docs():
        rag_storage.write_to_storage()
        push_to_repo(config)

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

    def complete_prompt(prompt):
        response = build_query_engine().query(prompt)
        logger.debug("Response from query engine: %s", response)
        return response

    def build_query_engine():
        return rag_storage.make_query_engine(
            llm=_engine["llm"], query_prompts=query_prompts_from_settings(settings)
        )

    @app.route("/trycompletion", methods=["POST"])
    def try_completion_api():
        prompt = request.json["prompt"]
        response = complete_prompt(prompt)
        return response_to_transport(response)

    def complete_chat(messages):
        new_message = messages[-1]
        history = [ChatMessage(**m) for m in messages[:-1]]
        response = rag_storage.make_chat_engine(
            llm=_engine["llm"], chat_prompts=chat_prompts_from_settings(settings)
        ).chat(new_message["content"], chat_history=history)
        logger.debug("Response from chat engine: %s", response)
        return response

    @app.route("/try-chat", methods=["POST"])
    def try_chat_api():
        prompt = request.json["messages"]
        response = complete_chat(prompt)
        return response_to_transport(response)

    @app.route("/inference-container-details", methods=["POST"])
    def inference_container_details_api():
        return {"message": "Inference container details"}

    @app.route(
        "/last-checkpoint",
    )
    def last_checkpoint_api():
        last_commit = get_last_commit(config["repo_name"])
        if last_commit is None:
            return {"latest_change_time": None}
        return {"latest_change_time": last_commit.created_at}

    @app.post("/update-model")
    def update_model():
        del _engine["llm"]
        gc.collect()
        if request.json.get("clear_space") == True:
            model_builder.clear_vllm_models_folder()

        logger.info("Loading the model %s", request.json["model_name"])
        settings["model"] = request.json["model_name"]
        push_settings_update(config, settings)

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

    @app.route("/chat-prompts")
    def chat_prompts():
        return chat_prompts_from_settings(settings)

    @app.post("/update-chat-prompts")
    def update_chat_prompts():
        chat_prompts = request.json
        settings["chat_prompts"] = chat_prompts
        push_settings_update(config, settings)
        return {"message": "Chat prompts updated"}

    @app.route("/query-prompts")
    def query_prompts():
        return query_prompts_from_settings(settings)

    @app.post("/update-app-name")
    def update_app_name():
        app_name = request.json["app_name"]
        settings["app_name"] = app_name
        push_settings_update(config, settings)
        return {"message": "App name updated"}

    @app.route("/app-name")
    def get_app_name():
        return {"app_name": app_name_from_settings(settings)}

    @app.post("/update-query-prompts")
    def update_query_prompts():
        query_prompts = request.json
        settings["query_prompts"] = query_prompts
        push_settings_update(config, settings)
        return {"message": "Query prompts updated"}

    @app.route("/logs")
    def logs():
        # The number of lines to return is an optional query param
        num_lines = request.args.get("num_lines", default=100, type=int)
        return {"logs": tail_logs(LOG_FILE_FOLDER, num_lines)}

    @app.post("/api/evaluation/retrieval/autorun")
    async def autorun_retrieval_eval_api():
        raw_res = await evaluate_on_auto_dataset(
            build_query_engine(), _engine["llm"], rag_storage.get_nodes()
        )
        return [retrieval_eval_result_to_transport(rag_storage, re) for re in raw_res]

    def format_for_display(eval_result):
        if len(eval_result["expected_texts"]) != 1:
            raise ValueError("Expected texts should be a list of length 1")
        if len(eval_result["retrieved_texts"]) != 2:
            raise ValueError("Retrieved texts should be a list of length 2")
        return {
            "query": eval_result["query"],
            "expected_text": eval_result["expected_texts"][0],
            "retrieved_text_0": eval_result["retrieved_texts"][0],
            "retrieved_text_1": eval_result["retrieved_texts"][1],
            "precision": eval_result["metrics"]["precision"],
            "recall": eval_result["metrics"]["recall"],
            "hit_rate": eval_result["metrics"]["hit_rate"],
        }

    @app.post("/evaluation/retrieval/autorun")
    async def retrieval_eval_autorun_view():
        # with open("data/sample_retrieval_eval.json") as f:
        #     dummy_content = json.load(f)
        content = await autorun_retrieval_eval_api()
        to_display = [format_for_display(res) for res in content]
        return render_template("retrieval_eval_result.html", content=to_display)

    @app.route("/")
    def home():
        content = data_api()
        return render_template("main.html", content=content)

    @app.route("/api/data")
    def data_api():
        return {
            "llm_model": settings["model"],
            "app_name": app_name_from_settings(settings),
            "repo_name": config["repo_name"],
            "files": list_files_api()["files"],
            "embed_model": DEFAULT_EMBEDDING_MODEL,
            "completion": "",
            "last_checkpoint": last_checkpoint_api()["latest_change_time"],
            "chat_prompts": chat_prompts(),
            "query_prompts": query_prompts(),
        }

    return app
