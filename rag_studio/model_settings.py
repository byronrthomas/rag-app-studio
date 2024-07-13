import json
from llama_index.core.chat_engine.condense_plus_context import (
    DEFAULT_CONDENSE_PROMPT_TEMPLATE,
    DEFAULT_CONTEXT_PROMPT_TEMPLATE,
)
from llama_index.core.prompts.default_prompts import (
    DEFAULT_REFINE_PROMPT_TMPL,
    DEFAULT_TEXT_QA_PROMPT_TMPL,
)

DEFAULT_LLM_MODEL = "mistralai/Mistral-7B-Instruct-v0.1"
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
DEFAULT_APP_NAME = "RAG Studio Application"


def query_prompts_from_settings(settings):
    default_prompts = {
        "text_qa_template": DEFAULT_TEXT_QA_PROMPT_TMPL,
        "refine_template": DEFAULT_REFINE_PROMPT_TMPL,
    }
    return settings.get("query_prompts", default_prompts)


def chat_prompts_from_settings(settings):
    default_prompts = {
        "condense_prompt": DEFAULT_CONDENSE_PROMPT_TEMPLATE,
        "context_prompt": DEFAULT_CONTEXT_PROMPT_TEMPLATE,
    }
    return settings.get("chat_prompts", default_prompts)


def app_name_from_settings(settings):
    return settings.get("app_name", DEFAULT_APP_NAME)


def read_settings(settings_path):
    with open(settings_path, "r", encoding="UTF-8") as f:
        return json.load(f)
