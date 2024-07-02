from unittest.mock import MagicMock
import pytest

from rag_studio.webserver import create_app


@pytest.fixture(name="mock_engine")
def mock_engine_fixture():
    return {"embed_model": MagicMock(), "llm": MagicMock()}


@pytest.fixture(name="nogpu_client_factory")
def client_factory_fixture(mock_engine):
    def create_client(config):
        app = create_app(config=config, _engine=mock_engine)
        return app.test_client()

    return create_client


@pytest.fixture(name="app_nogpu")
def app_nogpu_fixture(mock_engine, test_config):
    app = create_app(config=test_config, _engine=mock_engine)
    return app


@pytest.fixture(name="client_nogpu")
def client_nogpu_fixture(app_nogpu):
    return app_nogpu.test_client()


@pytest.mark.createsRepo
def test_when_launched_without_repo_model_is_initially_default(app_nogpu):
    assert True == False, "TODO: Implement test"


def test_when_launched_with_repo_id_set_loads_from_repo(app_nogpu, config_with_repo):
    assert True == False, "TODO: Implement test"


def test_when_launched_with_repo_id_set_doesnt_change_repo(
    nogpu_client_factory, config_with_repo
):
    client = nogpu_client_factory(config_with_repo)
    repo_result = client.get("/repo_name")
    assert repo_result.status_code == 200
    repo_data = repo_result.json
    assert repo_data["repo_name"] == "test-model-1"


@pytest.mark.createsRepo
def test_when_launched_without_repo_id_creates_new_repo_with_config(app_nogpu):
    assert True == False, "TODO: Implement test"


def test_after_model_changed_reports_new_model(app_nogpu, config_with_repo):
    assert True == False, "TODO: Implement test"


def test_after_model_changed_repo_has_new_model(app_nogpu, config_with_repo):
    assert True == False, "TODO: Implement test"
