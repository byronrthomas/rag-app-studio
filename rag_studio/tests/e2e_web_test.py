import pytest

from rag_studio.hf_repo_storage import api
from rag_studio.studio_webserver import create_app
from rag_studio.tests.conftest import (
    TEST_PREFS_REPO,
    TEST_REPO_NAME,
    push_initial_repo_prefs,
)


@pytest.fixture(name="e2e_withgpu_app")
def app_fixture(test_config):
    # Ensure we will construct a new repo for storage
    push_initial_repo_prefs(api.get_full_repo_name(TEST_PREFS_REPO), None)
    app = create_app(test_config)
    print("App fixture created")
    # other setup can go here

    yield app

    # clean up / reset resources here
    push_initial_repo_prefs(api.get_full_repo_name(TEST_PREFS_REPO), TEST_REPO_NAME)


@pytest.fixture(name="e2e_withgpu_client")
def client_fixture(e2e_withgpu_app):
    return e2e_withgpu_app.test_client()


def healthcheck_works(client):
    response = client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json["message"] == "API is running!"
    assert "start_time" in response.json


def check_file_list(client, exp_file_list):
    response = client.get("/files")
    assert response.status_code == 200
    assert response.json["files"] == exp_file_list


def upload_file(client):

    data = {"file": (open("data/paul_graham_essay.txt", "rb"), "paul_graham_essay.txt")}
    response = client.post("/upload", data=data)
    assert response.status_code == 200
    assert response.json["message"] == "File uploaded successfully"


def try_completion_api(client):
    data = {"prompt": "What did the author do growing up?"}
    response = client.post("/trycompletion", json=data)
    assert response.status_code == 200
    assert isinstance(response.json["completion"], str)
    assert response.json["completion"] != ""
    return response.json["completion"]


def last_checkpoint_api(client):
    response = client.get("/last-checkpoint")
    assert response.status_code == 200
    return response.json["latest_change_time"]


@pytest.mark.createsRepo
@pytest.mark.needsGpu
def test_e2e_smoke_test(e2e_withgpu_client):
    healthcheck_works(e2e_withgpu_client)

    # Check file list is empty
    exp_file_list = []
    check_file_list(e2e_withgpu_client, exp_file_list)

    # Check completion API
    initial_completion = try_completion_api(e2e_withgpu_client)
    initial_checkpoint = last_checkpoint_api(e2e_withgpu_client)

    # Upload a file
    upload_file(e2e_withgpu_client)
    check_file_list(e2e_withgpu_client, ["paul_graham_essay.txt"])
    # Should have been checkpointed automatically
    checkpoint_2 = last_checkpoint_api(e2e_withgpu_client)
    assert checkpoint_2 != initial_checkpoint

    # Check completion API
    completion_2 = try_completion_api(e2e_withgpu_client)
    assert initial_completion != completion_2

    # Make a checkpoint
    # response = client.post("/checkpoint", json={})
    # assert response.status_code == 200
    # assert response.json["message"] == "Checkpoint OK"

    # Check last checkpoint time
    last_checkpoint = last_checkpoint_api(e2e_withgpu_client)
    assert last_checkpoint == checkpoint_2

    # Finally try to change the LLM model
    data = {
        "model_name": "google/gemma-2b"
        # , "clear_space": True
    }
    response = e2e_withgpu_client.post("/model", json=data)
    assert response.status_code == 200
    assert response.json["message"] == "Model updated"

    model_name = e2e_withgpu_client.get("/model-name").json["model_name"]
    assert model_name == "google/gemma-2b"

    completion_3 = try_completion_api(e2e_withgpu_client)
    assert completion_3 != completion_2

    # Check last checkpoint time
    last_checkpoint = last_checkpoint_api(e2e_withgpu_client)
    assert last_checkpoint != checkpoint_2
