import pytest


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
def test_e2e_smoke_test(client):
    healthcheck_works(client)

    # Check file list is empty
    exp_file_list = []
    check_file_list(client, exp_file_list)

    # Check completion API
    initial_completion = try_completion_api(client)
    initial_checkpoint = last_checkpoint_api(client)

    # Upload a file
    upload_file(client)
    check_file_list(client, ["paul_graham_essay.txt"])
    # Should have been checkpointed automatically
    checkpoint_2 = last_checkpoint_api(client)
    assert checkpoint_2 != initial_checkpoint

    # Check completion API
    completion_2 = try_completion_api(client)
    assert initial_completion != completion_2

    # Make a checkpoint
    # response = client.post("/checkpoint", json={})
    # assert response.status_code == 200
    # assert response.json["message"] == "Checkpoint OK"

    # Check last checkpoint time
    last_checkpoint = last_checkpoint_api(client)
    assert last_checkpoint == checkpoint_2

    # Finally try to change the LLM model
    data = {
        "model_name": "google/gemma-2b"
        # , "clear_space": True
    }
    response = client.post("/model", json=data)
    assert response.status_code == 200
    assert response.json["message"] == "Model updated"

    model_name = client.get("/model-name").json["model_name"]
    assert model_name == "google/gemma-2b"

    completion_3 = try_completion_api(client)
    assert completion_3 != completion_2

    # Check last checkpoint time
    last_checkpoint = last_checkpoint_api(client)
    assert last_checkpoint != checkpoint_2
