import os
import json
import logging

from rag_studio.hf_repo_storage import download_file, repo_exists

logger = logging.getLogger(__name__)

PREFERENCES_REPO_NAME = "rag-app-studio-preferences"


def infer_prefs_repo_id():
    return os.environ.get("__TEST_PREFS_REPO_ID__", PREFERENCES_REPO_NAME)


def fetch_preferences(prefs_repo_dir, prefs_repo_id):
    download_file(prefs_repo_id, "preferences.json", prefs_repo_dir)
    with open(f"{prefs_repo_dir}/preferences.json", "r", encoding="UTF-8") as f:
        prefs = json.load(f)
    return prefs


def infer_repo_id(prefs_repo_dir):
    if os.environ.get("RAG_REPO_ID"):
        return os.environ["RAG_REPO_ID"]
    prefs_repo_id = infer_prefs_repo_id()
    if not repo_exists(prefs_repo_id):
        raise RuntimeError(f"Preferences repo {prefs_repo_id} does not exist")
    prefs = fetch_preferences(prefs_repo_dir, prefs_repo_id)

    logger.info("Loaded preferences %s", prefs)
    if not prefs.get("active_repo_id"):
        raise RuntimeError("No active repo set in preferences")
    return prefs["active_repo_id"]
