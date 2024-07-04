import logging

logger = logging.getLogger(__name__)


class ModelBuilder:
    def __init__(self, models_download_folder):
        self.models_download_folder = models_download_folder

    def derive_max_possible_model_len(self, llm_model):
        """Derive the max model length from the model name."""
        from vllm.config import _get_and_verify_max_len
        from vllm.transformers_utils.config import get_config, get_hf_text_config

        config = get_config(llm_model, trust_remote_code=True)
        text_config = get_hf_text_config(config)
        return _get_and_verify_max_len(text_config, None, False, None)

    def make_embedding_model(self, model_name):
        """Initialise the embedding model with the given config."""
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding

        # embedding model
        return HuggingFaceEmbedding(
            model_name=model_name,
            cache_folder=f"{self.models_download_folder}/.hf-cache",
        )

    def make_llm(self, llm_model):
        """Initialise the LLM model with the given config."""
        from llama_index.llms.vllm import Vllm
        import torch

        max_possible_model_len = self.derive_max_possible_model_len(llm_model)
        logger.info("Max possible model length: %d", max_possible_model_len)
        # Calculate number of available GPUs

        return Vllm(
            model=llm_model,
            download_dir=self.vllm_models_folder(),
            dtype="float16",
            tensor_parallel_size=torch.cuda.device_count(),
            vllm_kwargs={
                "max_model_len": min(max_possible_model_len, 30000),
            },
        )

    def vllm_models_folder(self):
        return f"{self.models_download_folder}/vllm-via-llama-models"

    def clear_vllm_models_folder(self):
        import shutil

        logger.info("Clearing models folder %s", self.vllm_models_folder())

        shutil.rmtree(self.vllm_models_folder(), ignore_errors=True)
