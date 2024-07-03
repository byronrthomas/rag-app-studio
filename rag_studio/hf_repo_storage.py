import os
import shutil
from huggingface_hub import login, HfApi
import secrets

import logging

logger = logging.getLogger(__name__)

# login()

api = HfApi()


def make_repo_name():
    """Create a unique repo name by appending a random hex string to a base name."""
    # Generate a random hex string of 4 bytes (8 characters)
    random_hex = secrets.token_hex(4)
    return f"rag-studio-{random_hex}"


def init_repo(existing_repo_name):
    """Initialise the repo, by choosing a new unique name if one is not provided.
    If the repo name is passed, it will be assumed to exist already."""
    repo_name = existing_repo_name
    if not repo_name:
        repo_name = make_repo_name()
        api.create_repo(repo_id=repo_name, private=True, exist_ok=False)
    return repo_name


def upload_folder(repo_name, model_path):
    repo_id = api.get_full_repo_name(repo_name)
    api.upload_folder(repo_id=repo_id, folder_path=model_path)


def download_from_repo(repo_name, local_path):
    all_files = list_files(repo_name)
    # filtered_files = [file for file in all_files if file.startswith("storage/")]
    # logger.info(
    #     "Repo %s has %d files, %d files are in storage path",
    #     repo_id,
    #     len(all_files),
    #     len(filtered_files),
    # )
    filtered_files = all_files
    # Clear out the local path
    shutil.rmtree(local_path, ignore_errors=True)
    os.makedirs(local_path, exist_ok=True)
    for fname in filtered_files:
        logger.info("Downloading %s to %s", fname, local_path)
        api.hf_hub_download(
            repo_id=api.get_full_repo_name(repo_name),
            filename=fname,
            local_dir=local_path,
        )


def download_file(repo_name, file_name, local_path):
    if not os.path.exists(local_path):
        os.makedirs(local_path)
    api.hf_hub_download(
        repo_id=api.get_full_repo_name(repo_name),
        filename=file_name,
        local_dir=local_path,
    )


def list_files(repo_name):
    repo_id = api.get_full_repo_name(repo_name)
    all_files = api.list_repo_files(repo_id=repo_id)
    return all_files


def get_last_commit(repo_name):
    commit_list = get_commits(repo_name)
    if len(commit_list) == 0:
        return None
    return commit_list[0]


def get_commits(repo_name):
    repo_id = api.get_full_repo_name(repo_name)
    commit_list = api.list_repo_commits(repo_id=repo_id)
    return commit_list
