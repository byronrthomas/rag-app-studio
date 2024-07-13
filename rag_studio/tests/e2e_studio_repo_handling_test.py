import os
import secrets
import pytest

from rag_studio.hf_repo_storage import api, repo_exists
from rag_studio.inference.repo_handling import fetch_preferences
from rag_studio.tests.conftest import (
    TEST_PREFS_REPO,
    TEST_REPO_NAME,
    push_initial_model_settings,
)
from rag_studio.tests.test_utils import make_temp_folder


@pytest.fixture(name="separate_prefs_repo")
def separate_prefs_repo_fixture():
    prefs_repo_name = f"prefs-repo-{secrets.token_hex(4)}"
    os.environ["__TEST_PREFS_REPO_ID__"] = prefs_repo_name
    yield prefs_repo_name
    if "__TEST_PREFS_REPO_ID__" in os.environ:
        del os.environ["__TEST_PREFS_REPO_ID__"]


@pytest.mark.createsRepo
def test_when_prefs_repo_doesnt_exist_gets_created(
    nogpu_client_factory, separate_prefs_repo
):
    assert not repo_exists(separate_prefs_repo)
    client = nogpu_client_factory()
    assert repo_exists(separate_prefs_repo)
    prefs = fetch_preferences(make_temp_folder(), separate_prefs_repo)
    # This one should be a dynamically created one
    assert prefs.get("active_repo_id") == client.get("/repo_name").json["repo_name"]


def test_when_prefs_repo_exists_loads_latest_repo_id(
    nogpu_client_factory, config_with_repo
):
    # Check precondition - because the fixture sets this to be TEST_REPO_NAME
    # this should work
    initial_prefs = fetch_preferences(make_temp_folder(), TEST_PREFS_REPO)
    assert initial_prefs.get("active_repo_id") == TEST_REPO_NAME
    # Use the config with repo - which exists
    client = nogpu_client_factory(config_with_repo)
    # and since the prefs initially set it this way, it should be returned fine
    assert client.get("/repo_name").json["repo_name"] == TEST_REPO_NAME


@pytest.mark.createsRepo
def test_when_prefs_repo_exists_provided_repo_id_overrides_it(
    nogpu_client_factory, config_with_repo
):
    repo_id = f"test-other-repo-{secrets.token_hex(4)}"
    api.create_repo(repo_id=repo_id, private=True, exist_ok=True)
    push_initial_model_settings(api.get_full_repo_name(repo_id))
    os.environ["RAG_REPO_ID"] = repo_id
    client = nogpu_client_factory(config_with_repo)
    prefs = fetch_preferences(make_temp_folder(), TEST_PREFS_REPO)
    assert prefs.get("active_repo_id") != repo_id
    assert client.get("/repo_name").json["repo_name"] == repo_id

    # Check that after updating something, the active repo gets set
    new_model = "new-model"
    resp = client.post("/model", json={"model_name": new_model})
    assert resp.status_code == 200
    prefs = fetch_preferences(make_temp_folder(), TEST_PREFS_REPO)
    assert prefs.get("active_repo_id") == repo_id


@pytest.fixture(name="fresh_app_env")
def fresh_app_env_var_fixture():
    os.environ["CREATE_NEW_RAG_APP"] = "true"
    if "RAG_REPO_ID" in os.environ:
        del os.environ["RAG_REPO_ID"]
    yield
    if "CREATE_NEW_RAG_APP" in os.environ:
        del os.environ["CREATE_NEW_RAG_APP"]


@pytest.mark.createsRepo
def test_when_prefs_repo_exists_create_fresh_repo_overrides_it(
    nogpu_client_factory, config_with_repo, fresh_app_env
):
    client = nogpu_client_factory(config_with_repo)
    prefs = fetch_preferences(make_temp_folder(), TEST_PREFS_REPO)
    assert prefs.get("active_repo_id") != TEST_REPO_NAME
    assert client.get("/repo_name").json["repo_name"] == prefs.get("active_repo_id")


def test_fails_if_create_new_app_and_repo_id_provided(
    nogpu_client_factory, config_with_repo, fresh_app_env
):
    repo_id = f"test-other-repo-{secrets.token_hex(4)}"
    os.environ["RAG_REPO_ID"] = repo_id
    with pytest.raises(
        ValueError,
        match="Cannot set both RAG_REPO_ID and CREATE_NEW_RAG_APP - drop RAG_REPO_ID if you want a fresh app",
    ):
        nogpu_client_factory(config_with_repo)
