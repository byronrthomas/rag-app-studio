import json
import os
import pytest

from rag_studio.hf_repo_storage import (
    download_from_repo,
    get_last_commit,
    list_files,
    api,
)
from rag_studio.model_settings import DEFAULT_APP_NAME, DEFAULT_LLM_MODEL
from rag_studio.tests.conftest import (
    TEST_INITIAL_MODEL,
    TEST_PREFS_REPO,
    TEST_REPO_NAME,
    push_initial_repo_prefs,
)
from rag_studio.tests.test_utils import cleanup_temp_folder, make_temp_folder
from rag_studio.studio_webserver import apply_defaults


@pytest.mark.createsRepo
def test_when_launched_without_repo_model_and_app_name_is_initially_default(
    nogpu_client_factory,
):
    # Ensure we will construct a new repo
    push_initial_repo_prefs(api.get_full_repo_name(TEST_PREFS_REPO), None)
    client = nogpu_client_factory()
    model_result = client.get("/model-name")
    assert model_result.status_code == 200
    model_data = model_result.json
    assert model_data["model_name"] == DEFAULT_LLM_MODEL
    app_name_result = client.get("/app-name")
    assert app_name_result.status_code == 200
    app_name_data = app_name_result.json
    assert app_name_data["app_name"] == DEFAULT_APP_NAME


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
    model_result = client.get("/model-name")
    assert model_result.status_code == 200
    model_data = model_result.json
    assert model_data["model_name"] == TEST_INITIAL_MODEL


def test_when_launched_with_repo_id_set_doesnt_change_repo(
    nogpu_client_factory, config_with_repo
):
    client = nogpu_client_factory(config_with_repo)
    repo_result = client.get("/repo_name")
    assert repo_result.status_code == 200
    repo_data = repo_result.json
    assert repo_data["repo_name"] == TEST_REPO_NAME


@pytest.mark.createsRepo
def test_when_launched_without_repo_id_creates_new_repo_with_config(
    nogpu_client_factory,
):
    # Ensure we will construct a new repo
    push_initial_repo_prefs(api.get_full_repo_name(TEST_PREFS_REPO), None)
    client = nogpu_client_factory()
    repo_result = client.get("/repo_name")
    assert repo_result.status_code == 200
    repo_data = repo_result.json
    assert repo_data["repo_name"] != TEST_REPO_NAME
    assert "model_settings.json" in list_files(repo_data["repo_name"])
    assert get_last_commit(repo_data["repo_name"]) is not None


def reset_model_settings(client):
    update_result = client.post("/model", json={"model_name": TEST_INITIAL_MODEL})
    assert update_result.status_code == 200


def test_after_model_changed_reports_new_model(nogpu_client_factory, config_with_repo):
    client = nogpu_client_factory(config_with_repo)
    update_result = client.post("/model", json={"model_name": "new-model"})
    assert update_result.status_code == 200
    model_result = client.get("/model-name")
    assert model_result.status_code == 200
    model_data = model_result.json
    assert model_data["model_name"] == "new-model"
    # Put the original model back
    reset_model_settings(client)


def test_after_model_changed_repo_has_new_model(nogpu_client_factory, config_with_repo):
    client = nogpu_client_factory(config_with_repo)
    update_result = client.post("/model", json={"model_name": "new-model"})
    assert update_result.status_code == 200
    # Construct a temp folder
    temp_folder = make_temp_folder()
    download_from_repo(TEST_REPO_NAME, temp_folder)
    assert os.path.exists(f"{temp_folder}/model_settings.json")
    with open(f"{temp_folder}/model_settings.json", "r", encoding="UTF-8") as f:
        model_data = json.load(f)
        assert model_data["model"] == "new-model"
    # Put the original model settings back
    reset_model_settings(client)
    cleanup_temp_folder(temp_folder)


def test_after_app_name_changed_reports_new_name(
    nogpu_client_factory, config_with_repo
):
    client = nogpu_client_factory(config_with_repo)
    update_result = client.post(
        "/name", json={"app_name": "Willy Wonka's fabulous RAG app"}
    )
    assert update_result.status_code == 200
    app_name_result = client.get("/app-name")
    assert app_name_result.status_code == 200
    app_name_data = app_name_result.json
    assert app_name_data["app_name"] == "Willy Wonka's fabulous RAG app"
    reset_model_settings(client)


def test_after_app_name_changed_repo_has_new_name(
    nogpu_client_factory, config_with_repo
):
    client = nogpu_client_factory(config_with_repo)
    update_result = client.post(
        "/name", json={"app_name": "Willy Wonka's fabulous RAG app"}
    )
    assert update_result.status_code == 200
    # Construct a temp folder
    temp_folder = make_temp_folder()
    download_from_repo(TEST_REPO_NAME, temp_folder)
    assert os.path.exists(f"{temp_folder}/model_settings.json")
    with open(f"{temp_folder}/model_settings.json", "r", encoding="UTF-8") as f:
        model_data = json.load(f)
        assert model_data["app_name"] == "Willy Wonka's fabulous RAG app"
    reset_model_settings(client)
    cleanup_temp_folder(temp_folder)
