import logging
import os
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
    PromptTemplate,
    load_index_from_storage,
)
from llama_index.core.ingestion import run_transformations
from llama_index.core.settings import transformations_from_settings_or_context
from llama_index.core.storage.docstore.types import RefDocInfo
from llama_index.core.prompts.prompt_type import PromptType

logger = logging.getLogger(__name__)


def safe_extract_filename(doc_info: RefDocInfo):
    mdata = doc_info.metadata
    return mdata.get("file_name")


class RagStore:
    def __init__(self, storage_root, embed_model=None):
        if not storage_root:
            raise ValueError("Storage root cannot be empty")
        self.storage_path = f"{storage_root}/index"
        if os.path.exists(self.storage_path):
            logger.info("Loading existing index from storage at %s", self.storage_path)
            # load the existing index
            storage_context = StorageContext.from_defaults(
                persist_dir=self.storage_path
            )
            self.index = load_index_from_storage(
                storage_context, embed_model=embed_model
            )
        else:
            logger.info("Beginning fresh index")
            self.index = VectorStoreIndex(nodes=[], embed_model=embed_model)

    def add_document(self, file_path):
        reader = SimpleDirectoryReader(input_files=[file_path])
        docs = reader.load_data()
        transformations = transformations_from_settings_or_context(Settings, None)
        nodes = run_transformations(docs, transformations)
        self.index.insert_nodes(nodes)
        logger.info("Added document %s of %d nodes to the index", file_path, len(nodes))

    def list_files(self):
        doc_info_by_id = self.index.docstore.get_all_ref_doc_info()
        return [safe_extract_filename(doc_info) for doc_info in doc_info_by_id.values()]

    def write_to_storage(self):
        logger.info("Persisting index to storage at %s", self.storage_path)
        self.index.storage_context.persist(persist_dir=self.storage_path)

    def make_query_engine(self, llm, query_prompts):
        kwargs = {}
        if query_prompts:
            kwargs["text_qa_template"] = PromptTemplate(
                query_prompts["text_qa_template"],
                prompt_type=PromptType.QUESTION_ANSWER,
            )
            kwargs["refine_template"] = PromptTemplate(
                query_prompts["refine_template"], prompt_type=PromptType.REFINE
            )
        return self.index.as_query_engine(llm=llm, **kwargs)

    def make_chat_engine(self, llm, chat_prompts):
        kwargs = {}
        if chat_prompts:
            kwargs["context_prompt"] = chat_prompts["context_prompt"]
            kwargs["condense_prompt"] = chat_prompts["condense_prompt"]
        return self.index.as_chat_engine(
            chat_mode="condense_plus_context", llm=llm, **kwargs
        )

    def get_nodes(self):
        return self.index.docstore.get_nodes(self.index.docstore.docs.keys())

    def get_node_text(self, node_id):
        return self.index.docstore.get_node(node_id).get_content()
