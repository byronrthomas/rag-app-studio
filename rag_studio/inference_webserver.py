from datetime import datetime
import os
import shutil
from pathlib import Path
import sys
import logging
import secrets


from fastapi import FastAPI, HTTPException


from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.vllm import Vllm

from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.schema import BaseComponent

# from flask_cors import CORS
from rag_studio.model_builder import ModelBuilder
from rag_studio.model_settings import (
    chat_prompts_from_settings,
    query_prompts_from_settings,
    read_settings,
)
from rag_studio.ragstore import RagStore
from rag_studio.hf_repo_storage import download_from_repo
from rag_studio.openai.schema import ChatCompletionRequest, CompletionRequest

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


app = FastAPI()


# Capture the current time
startTime = datetime.now()

# Need to wire in the RAG storage initialisation here, based on path
# from config object
rag_storage_path = os.environ.get("RAG_STORAGE_PATH", "/tmp/rag_storage")
logger.info("RAG storage path: %s", rag_storage_path)
rag_repo_id = os.environ.get("RAG_REPO_ID")
if rag_repo_id is None:
    logger.error("RAG_REPO_ID is not set")
    sys.exit(1)

model_download_dir = os.environ.get("MODEL_DOWNLOAD_DIR", "/tmp/models")
logger.info("Model storage path: %s", model_download_dir)
# Need to download the repo into the storage path, then can just initialise the store
# from that path
if os.path.exists(rag_storage_path):
    logger.info("RAG storage path exists, removing before download")
    # Remove the directory tree at rag_storage_path, even if the dir is not empty
    shutil.rmtree(rag_storage_path)

model_builder = ModelBuilder(model_download_dir)

download_from_repo(rag_repo_id, rag_storage_path)
rag_storage = RagStore(
    rag_storage_path,
    embed_model=model_builder.make_embedding_model("BAAI/bge-large-en-v1.5"),
)
# Read model settings from the downloaded repo
model_settings_path = f"{rag_storage_path}/model_settings.json"
settings = read_settings(model_settings_path)
logger.info("Settings on startup: %s", settings)


@app.route("/healthcheck")
def healthcheck_api():
    """Healthcheck API to check if the API is running."""
    return {
        "message": "Inference API is running!",
        "start_time": startTime.strftime("%Y-%m-%d %H:%M:%S"),
    }


MODEL_NAME = settings["model"]
llm = model_builder.make_llm(MODEL_NAME)
chat_prompts = chat_prompts_from_settings(settings)
chat_engine = rag_storage.make_chat_engine(llm=llm, chat_prompts=chat_prompts)
query_prompts = query_prompts_from_settings(settings)
query_engine = rag_storage.make_query_engine(llm=llm, query_prompts=query_prompts)


@app.get("/query-prompts")
def get_query_prompts():
    """API to get the query prompts."""
    return query_prompts


@app.get("/chat-prompts")
def get_chat_prompts():
    """API to get the chat prompts."""
    return chat_prompts


@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest):
    """API to get completions for a given prompt."""
    req_id = secrets.token_hex(16)
    logger.info("Request ID: %s", req_id)
    messages = req.messages
    new_message = messages[-1]
    if new_message.get("role") != "user":
        raise HTTPException(
            status_code=400,
            detail=f"last message should be from user, but role was: {new_message.get('role')}",
        )
    history = [ChatMessage(**m) for m in messages[:-1]]

    problem_str = req.set_model_params_from_request(llm)
    if problem_str:
        return HTTPException(status_code=400, detail=problem_str)
    result = chat_engine.chat(messages[-1], chat_history=history)
    return skeleton_openai_chat_response(req_id, result.response, MODEL_NAME)


@app.post("/v1/completions")
def completions(req: CompletionRequest):
    """API to get completions for a given prompt."""
    req_id = secrets.token_hex(16)
    logger.info("Request ID: %s", req_id)
    problem_str = req.set_model_params_from_request(llm)
    if problem_str:
        return HTTPException(status_code=400, detail=problem_str)
    result = query_engine.query(req.prompt)
    return skeleton_openai_completion_response(req_id, result.response, MODEL_NAME)
