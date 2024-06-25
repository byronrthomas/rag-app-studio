import os
import sys
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
    load_index_from_storage,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.vllm import Vllm
import logging

MODEL_LOG_LEVEL = (
    logging.DEBUG
    if os.environ.get("USE_MODEL_DEBUG_LOGGING", "True") == "True"
    else logging.INFO
)

logging.basicConfig(stream=sys.stdout, level=MODEL_LOG_LEVEL)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

logger = logging.getLogger(__name__)

STORAGE_BASE_DIR = "/workspace/models"
PERSIST_DIR = "/workspace/storage"

# bge-base embedding model
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-large-en-v1.5", cache_folder=f"{STORAGE_BASE_DIR}/.hf-cache"
)

# VLLM model
Settings.llm = Vllm(
    model="mistralai/Mistral-7B-Instruct-v0.1",
    # model="bigcode/starcoder2-3b",
    download_dir=f"{STORAGE_BASE_DIR}/vllm-via-llama-models",
    vllm_kwargs={"max_model_len": 30000},
)

# check if storage already exists
if not os.path.exists(PERSIST_DIR):
    logger.info("Recreating index...")
    # load the documents and create the index
    documents = SimpleDirectoryReader("./data").load_data()
    index = VectorStoreIndex.from_documents(documents)
    # store it for later
    index.storage_context.persist(persist_dir=PERSIST_DIR)
else:
    logger.info("Loading existing index...")
    # load the existing index
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)


logger.info("Creating query engine...")
query_engine = index.as_query_engine()
response = query_engine.query("What did the author do growing up?")
print("\n\n\n\nResponse from query engine:")
print(response)
print("\n\n\n\n")
