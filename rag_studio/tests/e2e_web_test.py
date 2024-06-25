def test_healthcheck_works(client):
    response = client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json["message"] == "API is running!"
    assert "start_time" in response.json
