import pytest
import shutil
import os
import logging
from unittest.mock import MagicMock
from huggingface_hub import HfApi
from rag_studio.hf_repo_storage import repo_exists
from rag_studio.tests.test_utils import make_temp_folder
from rag_studio.studio_webserver import create_app

logger = logging.getLogger(__name__)

TEST_PREFS_REPO = "test-rag-studio-prefs"
TEST_REPO_NAME = "test-rag-studio-repo-1"
TEST_INITIAL_MODEL = "test-llm-model-1"
api = HfApi()


def push_initial_model_settings(repo_full_id):
    temp_folder = make_temp_folder()

    with open(f"{temp_folder}/model_settings.json", "w", encoding="UTF-8") as f:
        f.write('{"model": "' + TEST_INITIAL_MODEL + '"}')
    api.upload_folder(repo_id=repo_full_id, folder_path=temp_folder)


def push_initial_repo_prefs(repo_full_id, rag_repo_id):
    temp_folder = make_temp_folder()

    with open(f"{temp_folder}/preferences.json", "w", encoding="UTF-8") as f:
        if rag_repo_id is None:
            f.write("{}")
        else:
            f.write('{"active_repo_id": "' + rag_repo_id + '"}')
    api.upload_folder(repo_id=repo_full_id, folder_path=temp_folder)


@pytest.fixture(name="test_prefs_repo")
def test_prefs_repo_fixture():
    # Keep tests isolated from production by overriding the prefs repo name
    os.environ["__TEST_PREFS_REPO_ID__"] = TEST_PREFS_REPO
    if not repo_exists(TEST_PREFS_REPO):
        api.create_repo(TEST_PREFS_REPO, private=True, exist_ok=False)
    push_initial_repo_prefs(api.get_full_repo_name(TEST_PREFS_REPO), TEST_REPO_NAME)
    yield TEST_PREFS_REPO
    if "__TEST_PREFS_REPO_ID__" in os.environ:
        del os.environ["__TEST_PREFS_REPO_ID__"]


@pytest.fixture(name="test_config")
def test_config_fixture(test_prefs_repo):
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
    # Always reset to the initial settings
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


@pytest.fixture(name="mock_models")
def mock_model_builder():
    return MagicMock()


@pytest.fixture(name="nogpu_client_factory")
def client_factory_fixture(mock_models, test_config):
    def create_client(config=test_config):
        app = create_app(config=config, model_builder=mock_models)
        return app.test_client()

    return create_client
