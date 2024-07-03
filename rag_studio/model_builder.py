class ModelBuilder:
    def __init__(self, models_download_folder):
        self.models_download_folder = models_download_folder

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

        return Vllm(
            model=llm_model,
            download_dir=f"{self.models_download_folder}/vllm-via-llama-models",
            vllm_kwargs={"max_model_len": 30000},
        )
