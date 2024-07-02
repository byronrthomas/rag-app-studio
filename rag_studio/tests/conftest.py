import pytest
import shutil
import os
from rag_studio.webserver import create_app, inference_engine
import logging
from huggingface_hub import HfApi

logger = logging.getLogger(__name__)


@pytest.fixture(name="engine", scope="session")
def engine_fixture():
    logger.info("Creating engine fixture")
    return inference_engine({})


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
    api = HfApi()
    TEST_REPO_NAME = "test-model-1"
    api.create_repo(repo_id=TEST_REPO_NAME, private=True, exist_ok=True)
    return {**test_config, "REPO_NAME": TEST_REPO_NAME}


@pytest.fixture(name="app")
def app_fixture(engine, test_config):
    app = create_app(test_config, _engine=engine)

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
