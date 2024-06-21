import sys
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.vllm import Vllm
import logging

MODEL_LOG_LEVEL = logging.DEBUG

logging.basicConfig(stream=sys.stdout, level=MODEL_LOG_LEVEL)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

logger = logging.getLogger(__name__)

documents = SimpleDirectoryReader("data").load_data()

STORAGE_BASE_DIR = "/workspace/models"

# bge-base embedding model
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-base-en-v1.5", cache_folder=f"{STORAGE_BASE_DIR}/.hf-cache"
)

# VLLM model
Settings.llm = Vllm(
    model="mistralai/Mistral-7B-Instruct-v0.1",
    # model="bigcode/starcoder2-3b",
    download_dir=f"{STORAGE_BASE_DIR}/vllm-via-llama-models",
    vllm_kwargs={"max_model_len": 30000},
)

logger.info("Creating index...")
index = VectorStoreIndex.from_documents(
    documents,
)

logger.info("Creating query engine...")
query_engine = index.as_query_engine()
response = query_engine.query("What did the author do growing up?")
print("\n\n\n\nResponse from query engine:")
print(response)
print("\n\n\n\n")
