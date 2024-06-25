from huggingface_hub import login, HfApi

import logging

logger = logging.getLogger(__name__)

# login()

api = HfApi()


def create_repo():
    repo_name = "test-model-1"
    api.create_repo(repo_id=repo_name, private=True, exist_ok=True)
    return repo_name


def upload_folder(repo_name, model_path):
    repo_id = api.get_full_repo_name(repo_name)
    api.upload_folder(repo_id=repo_id, folder_path=model_path)


def download_from_repo(repo_name, local_path):
    repo_id = api.get_full_repo_name(repo_name)
    all_files = api.list_repo_files(repo_id=repo_id)
    filtered_files = [file for file in all_files if file.startswith("storage/")]
    logger.info(
        "Repo %s has %d files, %d files are in storage path",
        repo_id,
        len(all_files),
        len(filtered_files),
    )
    for fname in filtered_files:
        logger.info("Downloading %s to %s", fname, local_path)
        api.hf_hub_download(repo_id=repo_id, filename=fname, local_dir=local_path)
