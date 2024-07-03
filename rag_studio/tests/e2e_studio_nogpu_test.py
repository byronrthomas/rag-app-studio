import os
from unittest.mock import MagicMock, patch
import pytest

from rag_studio.hf_repo_storage import get_last_commit, list_files
from rag_studio.webserver import apply_defaults, create_app
import rag_studio.webserver as ws


@pytest.fixture(name="mock_models")
def mock_model_builder():
    return MagicMock()


@pytest.fixture(name="nogpu_client_factory")
def client_factory_fixture(mock_models, test_config):
    def create_client(config=test_config):
        app = create_app(config=config, model_builder=mock_models)
        return app.test_client()

    return create_client


@pytest.mark.createsRepo
def test_when_launched_without_repo_model_is_initially_default(nogpu_client_factory):
    assert True == False, "TODO: Implement test"


def test_when_launched_with_repo_id_set_loads_from_repo(
    nogpu_client_factory, config_with_repo
):
    # Let's put a dummy file in the config location
    # to prove that the config is being pulled from the repo
    model_settings_path = apply_defaults(config_with_repo)["model_settings_path"]
    # Ensure any folders that need creating are created
    os.makedirs(os.path.dirname(model_settings_path), exist_ok=True)
    with open(model_settings_path, "w", encoding="UTF-8") as f:
        f.write('{"model": "some-other-model"}')
    client = nogpu_client_factory(config_with_repo)
    model_result = client.get("/model_name")
    assert model_result.status_code == 200
    model_data = model_result.json
    assert model_data["model_name"] == "test-model-1"


def test_when_launched_with_repo_id_set_doesnt_change_repo(
    nogpu_client_factory, config_with_repo
):
    client = nogpu_client_factory(config_with_repo)
    repo_result = client.get("/repo_name")
    assert repo_result.status_code == 200
    repo_data = repo_result.json
    assert repo_data["repo_name"] == "test-model-1"


@pytest.mark.createsRepo
def test_when_launched_without_repo_id_creates_new_repo_with_config(
    nogpu_client_factory,
):
    client = nogpu_client_factory()
    repo_result = client.get("/repo_name")
    assert repo_result.status_code == 200
    repo_data = repo_result.json
    assert repo_data["repo_name"] != "test-model-1"
    assert list_files(repo_data["repo_name"]) == ["model_settings.json"]
    assert get_last_commit(repo_data["repo_name"]) is not None


def test_after_model_changed_reports_new_model(nogpu_client_factory, config_with_repo):
    client = nogpu_client_factory(config_with_repo)
    update_result = client.post("/model", json={"model_name": "new-model"})
    assert update_result.status_code == 200
    model_result = client.get("/model-name")
    assert model_result.status_code == 200
    model_data = model_result.json
    assert model_data["model_name"] == "new-model"


def test_after_model_changed_repo_has_new_model(nogpu_client_factory, config_with_repo):
    assert True == False, "TODO: Implement test"
