import pytest
import shutil
import os
from rag_studio.webserver import create_app, inference_engine
import logging

logger = logging.getLogger(__name__)


@pytest.fixture(name="engine", scope="session")
def engine_fixture():
    logger.info("Creating engine fixture")
    return inference_engine({})


@pytest.fixture(name="app")
def app_fixture(engine):
    test_config = {
        "TESTING": True,
        "rag_storage_path": "/tmp/rag_storage",
    }
    # Ensure storage path cleared out before each test
    if os.path.exists(test_config["rag_storage_path"]):
        logger.info("Clearing out storage path %s", test_config["rag_storage_path"])
        shutil.rmtree(test_config["rag_storage_path"], ignore_errors=False)

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
