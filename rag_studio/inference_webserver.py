from datetime import datetime
import os
import shutil
from pathlib import Path
import sys
from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
from rag_studio.ragstore import RagStore
from rag_studio.hf_repo_storage import get_last_commit, download_from_repo
import logging
from llama_index.core import (
    Settings,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.vllm import Vllm
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.schema import BaseComponent
import secrets

logger = logging.getLogger(__name__)


def make_llm(llm_model, download_dir):
    """Initialise the LLM model with the given config."""
    return Vllm(
        model=llm_model,
        download_dir=download_dir,
        vllm_kwargs={"max_model_len": 30000},
    )


def make_embed_model(model_name, cache_folder):
    """Initialise the embedding model with the given config."""
    return HuggingFaceEmbedding(
        model_name=model_name,
        cache_folder=cache_folder,
    )


def from_env_or_config(env_var, config, default=None):
    """Get the value from the environment variable or the config."""
    return os.environ.get(env_var, config.get(env_var)) or default


def set_model_params_from_request(llm: Vllm, data):
    """Set the model parameters from the request data."""
    # temperature: float = 1.0,
    # n: int = 1,
    # presence_penalty: float = 0.0,
    # frequency_penalty: float = 0.0,
    # top_p: float = 1.0,
    # stop: Optional[List[str]] = None,
    # max_tokens ->    # max_new_tokens: int = 512,
    # logprobs: Optional[int] = None,
    logger.info(
        "Setting model params from request data: %s",
        {k: v for k, v in data.items() if k not in {"messages", "prompt"}},
    )
    if "temperature" in data:
        llm.temperature = data["temperature"]
    if "n" in data and data["n"] != 1:
        logger.error("Currently returning n > 1 completions is unsupported")
        # llm.n = data["n"]
        return "Currently returning n > 1 completions is unsupported"
    if "presence_penalty" in data:
        llm.presence_penalty = data["presence_penalty"]
    if "frequency_penalty" in data:
        llm.frequency_penalty = data["frequency_penalty"]
    if "top_p" in data:
        llm.top_p = data["top_p"]
    if "stop" in data:
        llm.stop = data["stop"]
    if "max_tokens" in data:
        llm.max_new_tokens = data["max_tokens"]
    if "logprobs" in data:
        # llm.logprobs = data["logprobs"]
        logger.error("Currently logprobs output is unsupported")
        return "Currently logprobs output is unsupported"
    if (
        "tools" in data
        or "tool_choice" in data
        or "functions" in data
        or "function_call" in data
    ):
        logger.error("Currently use of tools / functions is unsupported")
        return "Currently use of tools / functions is unsupported"
    # Additionally the old completions API supports:
    # best_of: Optional[int] = None,
    if "best_of" in data:
        llm.best_of = data["best_of"]

    return None


def skeleton_openai_chat_response(req_id, completion_response, model_name="rag-chat"):
    """Construct a response that's representative of OpenAI format responses,
    even though we don't have most of the data that would be needed to construct it.
    Just fill in what we don't have with blanks"""
    # Example OpenAI chat completion response:
    #     {
    #   "id": "chatcmpl-123",
    #   "object": "chat.completion",
    #   "created": 1677652288,
    #   "model": "gpt-3.5-turbo-0125",
    #   "system_fingerprint": "fp_44709d6fcb",
    #   "choices": [{
    #     "index": 0,
    #     "message": {
    #       "role": "assistant",
    #       "content": "\n\nHello there, how may I assist you today?",
    #     },
    #     "logprobs": null,
    #     "finish_reason": "stop"
    #   }],
    #   "usage": {
    #     "prompt_tokens": 9,
    #     "completion_tokens": 12,
    #     "total_tokens": 21
    #   }
    # }
    return {
        "id": f"chatcmpl-{req_id}",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": model_name,
        "system_fingerprint": req_id,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": completion_response,
                },
                "logprobs": None,
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": -1,
            "completion_tokens": -1,
            "total_tokens": -1,
        },
    }


def skeleton_openai_completion_response(
    req_id, completion_response, model_name="rag-query"
):
    """Construct a response that's representative of OpenAI format responses,
    even though we don't have most of the data that would be needed to construct it.
    Just fill in what we don't have with blanks"""
    # Example OpenAI completion response:
    #     {
    #   "id": "cmpl-uqkvlQyYK7bGYrRHQ0eXlWi7",
    #   "object": "text_completion",
    #   "created": 1589478378,
    #   "model": "gpt-3.5-turbo-instruct",
    #   "system_fingerprint": "fp_44709d6fcb",
    #   "choices": [
    #     {
    #       "text": "\n\nThis is indeed a test",
    #       "index": 0,
    #       "logprobs": null,
    #       "finish_reason": "length"
    #     }
    #   ],
    #   "usage": {
    #     "prompt_tokens": 5,
    #     "completion_tokens": 7,
    #     "total_tokens": 12
    #   }
    # }
    return {
        "id": f"cmpl-{req_id}",
        "object": "text_completion",
        "created": int(datetime.now().timestamp()),
        "model": model_name,
        "system_fingerprint": req_id,
        "choices": [
            {
                "text": completion_response,
                "index": 0,
                "logprobs": None,
                "finish_reason": "length",
            }
        ],
        "usage": {
            "prompt_tokens": -1,
            "completion_tokens": -1,
            "total_tokens": -1,
        },
    }


def create_app(config=None, _engine=None):
    """Create the main Flask app with the given config."""
    config = config or {}
    app = Flask(__name__)
    CORS(app)

    # Capture the current time
    startTime = datetime.now()

    # Need to wire in the RAG storage initialisation here, based on path
    # from config object
    rag_storage_path = from_env_or_config(
        "RAG_STORAGE_PATH", config, default="/tmp/rag_storage"
    )
    logger.info("RAG storage path: %s", rag_storage_path)
    rag_repo_id = from_env_or_config("RAG_REPO_ID", config)
    if rag_repo_id is None:
        logger.error("RAG_REPO_ID is not set")
        sys.exit(1)

    model_download_dir = from_env_or_config(
        "MODEL_DOWNLOAD_DIR", config, default="/tmp/models"
    )
    logger.info("Model storage path: %s", model_download_dir)
    # Need to download the repo into the storage path, then can just initialise the store
    # from that path
    if os.path.exists(rag_storage_path):
        logger.info("RAG storage path exists, removing before download")
        # Remove the directory tree at rag_storage_path, even if the dir is not empty
        shutil.rmtree(rag_storage_path)

    download_from_repo(rag_repo_id, rag_storage_path)
    rag_storage = RagStore(
        rag_storage_path,
        embed_model=make_embed_model(
            "BAAI/bge-large-en-v1.5", f"{model_download_dir}/.hf-cache"
        ),
    )

    @app.route("/healthcheck")
    def healthcheck_api():
        """Healthcheck API to check if the API is running."""
        return jsonify(
            {
                "message": "Inference API is running!",
                "start_time": startTime.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.1"
    llm = make_llm(
        MODEL_NAME,
        f"{model_download_dir}/vllm-via-llama-models",
    )
    chat_engine = rag_storage.make_chat_engine(llm=llm)
    query_engine = rag_storage.make_query_engine(llm=llm)

    @app.post("/v1/chat/completions")
    def chat_completions():
        """API to get completions for a given prompt."""
        req_id = secrets.token_hex(16)
        logger.info("Request ID: %s", req_id)
        data = request.json
        messages = data.get("messages")
        if messages is None:
            return jsonify({"error": "messages is required"}), 400
        new_message = messages[-1]
        if new_message.get("role") != "user":
            return jsonify({"error": "last message should be from user"}), 400
        history = [ChatMessage(**m) for m in messages[:-1]]

        problem_str = set_model_params_from_request(llm, data)
        if problem_str:
            return jsonify({"error": problem_str}), 400
        completions = chat_engine.chat(messages[-1], chat_history=history)
        return jsonify(
            skeleton_openai_chat_response(req_id, completions.response, MODEL_NAME)
        )

    @app.post("/v1/completions")
    def completions():
        """API to get completions for a given prompt."""
        req_id = secrets.token_hex(16)
        logger.info("Request ID: %s", req_id)
        data = request.json
        problem_str = set_model_params_from_request(llm, data)
        if problem_str:
            return jsonify({"error": problem_str}), 400
        completions = query_engine.query(data["prompt"])
        return jsonify(
            skeleton_openai_completion_response(
                req_id, completions.response, MODEL_NAME
            )
        )

    return app
