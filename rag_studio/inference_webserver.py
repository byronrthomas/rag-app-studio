from datetime import datetime
import os
import shutil
from pathlib import Path
import sys
import logging
import secrets
from typing import Union


from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


from llama_index.core.base.llms.types import ChatMessage

# from flask_cors import CORS
from rag_studio import LOG_FILE_FOLDER, attach_handlers
from rag_studio.chat_history import ChatHistory
from rag_studio.inference.repo_handling import infer_repo_id
from rag_studio.log_files import tail_logs
from rag_studio.model_builder import ModelBuilder
from rag_studio.model_settings import (
    DEFAULT_EMBEDDING_MODEL,
    app_name_from_settings,
    chat_prompts_from_settings,
    query_prompts_from_settings,
    read_settings,
)
from rag_studio.ragstore import RagStore
from rag_studio.hf_repo_storage import download_from_repo, get_last_commit
from rag_studio.openai.schema import ChatCompletionRequest, CompletionRequest

logger = logging.getLogger(__name__)


def skeleton_openai_chat_response(
    req_id, response_obj, model_name="rag-chat", include_contexts=False
):
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
    choice_obj = {
        "index": 0,
        "message": {
            "role": "assistant",
            "content": response_obj.response,
        },
        "logprobs": None,
        "finish_reason": "stop",
    }
    add_contexts_if_needed(response_obj, include_contexts, choice_obj)
    return {
        "id": f"chatcmpl-{req_id}",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": model_name,
        "system_fingerprint": req_id,
        "choices": [choice_obj],
        "usage": {
            "prompt_tokens": -1,
            "completion_tokens": -1,
            "total_tokens": -1,
        },
    }


def add_contexts_if_needed(response_obj, include_contexts, choice_obj):
    if include_contexts:
        choice_obj["contexts"] = [
            {
                "context": sn.text,
                "score": sn.score,
                "filename": sn.metadata.get("file_name"),
            }
            for sn in response_obj.source_nodes
        ]


def skeleton_openai_completion_response(
    req_id, responseObj, model_name="rag-query", include_contexts=False
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
    choice_obj = {
        "text": responseObj.response,
        "index": 0,
        "logprobs": None,
        "finish_reason": "length",
    }
    add_contexts_if_needed(responseObj, include_contexts, choice_obj)
    return {
        "id": f"cmpl-{req_id}",
        "object": "text_completion",
        "created": int(datetime.now().timestamp()),
        "model": model_name,
        "system_fingerprint": req_id,
        "choices": [choice_obj],
        "usage": {
            "prompt_tokens": -1,
            "completion_tokens": -1,
            "total_tokens": -1,
        },
    }


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Capture the current time
startTime = datetime.now()

# Need to wire in the RAG storage initialisation here, based on path
# from config object
rag_storage_path = os.environ.get("RAG_STORAGE_PATH", "/tmp/rag_storage")
logger.info("RAG storage path: %s", rag_storage_path)
rag_repo_id = infer_repo_id(os.environ.get("RAG_PREFS_PATH", "/tmp/rag_prefs"))
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
    embed_model=model_builder.make_embedding_model(DEFAULT_EMBEDDING_MODEL),
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
chat_history = ChatHistory()


@app.on_event("startup")
async def startup_event():
    uvi_logger = logging.getLogger("uvicorn")
    attach_handlers(uvi_logger)


@app.get("/query-prompts")
def get_query_prompts():
    """API to get the query prompts."""
    return query_prompts


@app.get("/chat-prompts")
def get_chat_prompts():
    """API to get the chat prompts."""
    return chat_prompts


@app.get("/model-name")
def get_model_name():
    """API to get the model name."""
    return {"model_name": MODEL_NAME}


@app.get("/app-name")
def get_app_name():
    """API to get the app name."""
    return {"app_name": app_name_from_settings(settings)}


@app.get("/logs")
def get_logs(num_lines: Union[int, None] = None):
    """API to get the logs."""
    return {"logs": tail_logs(LOG_FILE_FOLDER, num_lines or 100)}


@app.get("/chat-history/{user_id}")
def get_chat_history(user_id: str):
    """API to get the chat history for a user."""
    return chat_history.get_user_chat_history(user_id)


@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest, include_contexts: bool = False):
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
    if req.user:
        logger.info("Tracking chat history for user %s", req.user)
        chat_history.update_user_chat_history(
            user_id=req.user,
            prev_messages=messages[:-1],
            new_question=new_message,
            new_answer={"role": "assistant", "content": result.response},
        )

    return skeleton_openai_chat_response(
        req_id, result, MODEL_NAME, include_contexts=include_contexts
    )


@app.post("/v1/completions")
def completions(req: CompletionRequest, include_contexts: bool = False):
    """API to get completions for a given prompt."""
    req_id = secrets.token_hex(16)
    logger.info("Request ID: %s", req_id)
    problem_str = req.set_model_params_from_request(llm)
    if problem_str:
        return HTTPException(status_code=400, detail=problem_str)
    result = query_engine.query(req.prompt)
    return skeleton_openai_completion_response(
        req_id, result, MODEL_NAME, include_contexts=include_contexts
    )


file_infos = rag_storage.list_files()


@app.get("/api/data")
def get_data():
    """API to get the data."""
    last_commit = get_last_commit(rag_repo_id)
    last_commit_time = last_commit.created_at if last_commit else None
    return {
        "llm_model": settings["model"],
        "app_name": app_name_from_settings(settings),
        "repo_name": rag_repo_id,
        "files": file_infos,
        "embed_model": DEFAULT_EMBEDDING_MODEL,
        "completion": "",
        "last_checkpoint": last_commit_time,
        "chat_prompts": chat_prompts,
        "query_prompts": query_prompts,
    }


@app.get("/")
def read_root():
    return RedirectResponse("/index.html")


app.mount("/", StaticFiles(directory="rag_studio/runner_static"), name="static")
