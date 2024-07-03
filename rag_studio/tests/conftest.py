import pytest
import shutil
import os
from rag_studio.model_builder import ModelBuilder
from rag_studio.tests.test_utils import make_temp_folder
from rag_studio.webserver import create_app, apply_defaults
import logging
from huggingface_hub import HfApi

logger = logging.getLogger(__name__)

TEST_REPO_NAME = "test-rag-studio-repo-1"
TEST_INITIAL_MODEL = "test-llm-model-1"
api = HfApi()


def push_initial_model_settings(repo_full_id):
    temp_folder = make_temp_folder()

    with open(f"{temp_folder}/model_settings.json", "w", encoding="UTF-8") as f:
        f.write('{"model": "' + TEST_INITIAL_MODEL + '"}')
    api.upload_folder(repo_id=repo_full_id, folder_path=temp_folder)


@pytest.fixture(name="test_config")
def test_config_fixture():
    test_config = {
        "TESTING": True,
        "RAG_STORAGE_PATH": "/tmp/rag_storage",
    }
    # Ensure storage path cleared out before each test
    if os.path.exists(test_config["RAG_STORAGE_PATH"]):
        logger.info("Clearing out storage path %s", test_config["RAG_STORAGE_PATH"])
        shutil.rmtree(test_config["RAG_STORAGE_PATH"], ignore_errors=False)
    return test_config


@pytest.fixture(name="config_with_repo")
def preexisting_repo_fixture(test_config):
    # Create a repo for testing
    full_repo_id = api.get_full_repo_name(TEST_REPO_NAME)
    if not api.repo_exists(repo_id=full_repo_id):
        logger.info("Creating test repo %s", TEST_REPO_NAME)
        api.create_repo(repo_id=TEST_REPO_NAME, private=True, exist_ok=True)
        push_initial_model_settings(full_repo_id)

    return {**test_config, "REPO_NAME": TEST_REPO_NAME}


@pytest.fixture(name="app")
def app_fixture(test_config):
    app = create_app(test_config)
    print("App fixture created")
    # other setup can go here

    yield app

    # clean up / reset resources here


@pytest.fixture(name="client")
def client_fixture(app):
    return app.test_client()


@pytest.fixture(name="runner")
def runner_fixture(app):
    return app.test_cli_runner()
