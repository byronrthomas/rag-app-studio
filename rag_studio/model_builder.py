import gc
import logging

logger = logging.getLogger(__name__)


def get_desired_dtype(model_name, download_dir):
    from vllm.engine.arg_utils import EngineArgs

    eadict = (
        EngineArgs(
            model=model_name,
            download_dir=download_dir,
        )
        .create_engine_config()
        .to_dict()
    )
    return eadict["model_config"].dtype


def infer_dtype_to_use(model_name, download_dir):
    import torch

    desired_dtype = get_desired_dtype(model_name, download_dir)

    # Check if the GPU supports the dtype
    if desired_dtype == torch.bfloat16:
        compute_capability = torch.cuda.get_device_properties(0)
        if compute_capability.major < 8:
            logger.warning(
                "The model requires bfloat16, but the GPU does not support it. Falling back to float16."
            )
            return "float16"

    torch_dtype_names = {
        torch.float16: "float16",
        torch.float32: "float32",
        torch.float64: "float64",
        torch.bfloat16: "bfloat16",
    }
    if desired_dtype not in torch_dtype_names:
        raise ValueError(f"Unknown dtype: {desired_dtype}")
    logger.info(
        "No compatibility issues with the desired dtype - using %s",
        torch_dtype_names[desired_dtype],
    )
    return torch_dtype_names[desired_dtype]


def free_gpu_memory():
    import torch

    gc.collect()

    # Free the memory
    torch.cuda.empty_cache()
    torch.cuda.reset_max_memory_allocated()

    logger.info("GPU memory has been freed.")


def calculate_max_content_window(model_name, download_dir, inferred_dtype):
    from vllm.engine.arg_utils import EngineArgs
    import torch

    engine_args = EngineArgs(
        model=model_name,
        dtype=inferred_dtype,
        download_dir=download_dir,
        tensor_parallel_size=torch.cuda.device_count(),
    )
    engine_config = engine_args.create_engine_config()
    distributed_executor_backend = (
        engine_config.parallel_config.distributed_executor_backend
    )
    executor_class = None
    if distributed_executor_backend == "ray":
        from vllm.executor.ray_utils import initialize_ray_cluster

        initialize_ray_cluster(engine_config.parallel_config)
        from vllm.executor.ray_gpu_executor import RayGPUExecutor

        executor_class = RayGPUExecutor
    elif distributed_executor_backend == "mp":
        from vllm.executor.multiproc_gpu_executor import MultiprocessingGPUExecutor

        executor_class = MultiprocessingGPUExecutor
    else:
        from vllm.executor.gpu_executor import GPUExecutor

        executor_class = GPUExecutor

    ec1_dict = engine_config.to_dict()

    exec1 = executor_class(
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
    del exec1
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

        logger.info("Initialising embedding model %s", model_name)

        # embedding model
        return HuggingFaceEmbedding(
            model_name=model_name,
            cache_folder=f"{self.models_download_folder}/.hf-cache",
        )

    def make_llm(self, llm_model):
        """Initialise the LLM model with the given config."""
        from llama_index.llms.vllm import Vllm
        import torch

        logger.info("Initialising LLM model %s", llm_model)

        inferred_dtype = infer_dtype_to_use(llm_model, self.vllm_models_folder())
        max_possible_model_len = self.derive_max_possible_model_len(llm_model)
        logger.info("Max possible model length: %d", max_possible_model_len)

        free_gpu_memory()
        max_possible_content_window = calculate_max_content_window(
            llm_model, self.vllm_models_folder(), inferred_dtype
        )
        logger.info(
            "Max possible content window (based on available GPU cache): %d",
            max_possible_content_window,
        )
        # Need to clear the cache to avoid OOM errors
        free_gpu_memory()
        max_model_len = min(max_possible_model_len, max_possible_content_window)
        logger.info("Choosing max model length: %d", max_model_len)

        return Vllm(
            model=llm_model,
            download_dir=self.vllm_models_folder(),
            dtype=inferred_dtype,
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
