def test_healthcheck_works(client):
    response = client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json["message"] == "API is running!"
    assert "start_time" in response.json


def test_upload_file_works(client):

    data = {"file": (open("data/paul_graham_essay.txt", "rb"), "paul_graham_essay.txt")}
    response = client.post("/upload", data=data)
    assert response.status_code == 200
    assert response.json["message"] == "File uploaded successfully"


def test_file_appears_in_list_after_upload(client):

    data = {"file": (open("data/paul_graham_essay.txt", "rb"), "paul_graham_essay.txt")}
    response = client.post("/upload", data=data)
    assert response.status_code == 200

    response = client.get("/files")
    assert response.status_code == 200
    assert "paul_graham_essay.txt" in response.json["files"]


def test_try_completion_api(client):
    data = {"prompt": "What did the author do growing up?"}
    response = client.post("/trycompletion", json=data)
    assert response.status_code == 200
    assert isinstance(response.json["completion"], str)
    assert response.json["completion"] != ""


def test_completions_change_after_upload(client):
    data = {"prompt": "What did the author do growing up?"}
    response = client.post("/trycompletion", json=data)
    assert response.status_code == 200
    first_completion = response.json["completion"]

    data = {"file": (open("data/paul_graham_essay.txt", "rb"), "paul_graham_essay.txt")}
    response = client.post("/upload", data=data)
    assert response.status_code == 200

    data = {"prompt": "What did the author do growing up?"}
    response = client.post("/trycompletion", json=data)
    assert response.status_code == 200
    second_completion = response.json["completion"]

    assert first_completion != second_completion


def test_checkpoint_api(client):
    # Checkpoint info needs to change
    response = client.get("/last-checkpoint")
    assert response.status_code == 200
    last_checkpoint = response.json["latest_change_time"]

    # Let's upload a file first
    data = {"file": (open("data/paul_graham_essay.txt", "rb"), "paul_graham_essay.txt")}
    response = client.post("/upload", data=data)
    assert response.status_code == 200

    response = client.post("/checkpoint", json={})
    assert response.status_code == 200
    assert response.json["message"] == "Checkpoint OK"

    response = client.get("/last-checkpoint")
    assert response.status_code == 200
    assert response.json["latest_change_time"] != last_checkpoint
