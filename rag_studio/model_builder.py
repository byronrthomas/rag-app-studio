import gc
import logging

logger = logging.getLogger(__name__)


def calculate_max_content_window(model_name, download_dir):
    from vllm.engine.arg_utils import EngineArgs
    from vllm.executor.gpu_executor import GPUExecutor

    engine_args = EngineArgs(
        model=model_name,
        dtype="float16",
        download_dir=download_dir,
    )
    engine_config = engine_args.create_engine_config()
    ec1_dict = engine_config.to_dict()
    exec1 = GPUExecutor(
        model_config=ec1_dict["model_config"],
        cache_config=ec1_dict["cache_config"],
        parallel_config=ec1_dict["parallel_config"],
        scheduler_config=ec1_dict["scheduler_config"],
        device_config=ec1_dict["device_config"],
        lora_config=ec1_dict["lora_config"],
        vision_language_config=ec1_dict["vision_language_config"],
        speculative_config=ec1_dict["speculative_config"],
        load_config=ec1_dict["load_config"],
    )
    gpu_blocks, _ = exec1.determine_num_available_blocks()
    return gpu_blocks * ec1_dict["cache_config"].block_size


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

        max_possible_content_window = calculate_max_content_window(
            llm_model, self.vllm_models_folder()
        )
        logger.info(
            "Max possible content window (based on available GPU cache): %d",
            max_possible_content_window,
        )
        # Need to clear the cache to avoid OOM errors
        gc.collect()
        max_model_len = min(max_possible_model_len, max_possible_content_window)
        logger.info("Choosing max model length: %d", max_model_len)

        return Vllm(
            model=llm_model,
            download_dir=self.vllm_models_folder(),
            dtype="float16",
            # Calculate number of available GPUs
            tensor_parallel_size=torch.cuda.device_count(),
            vllm_kwargs={
                "max_model_len": max_model_len,
            },
        )

    def vllm_models_folder(self):
        return f"{self.models_download_folder}/vllm-via-llama-models"

    def clear_vllm_models_folder(self):
        import shutil

        logger.info("Clearing models folder %s", self.vllm_models_folder())

        shutil.rmtree(self.vllm_models_folder(), ignore_errors=True)
