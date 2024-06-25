import pytest
from rag_studio.webserver import create_app


@pytest.fixture(name="app")
def app_fixture():
    app = create_app()
    app.config.update(
        {
            "TESTING": True,
        }
    )

    # other setup can go here

    yield app

    # clean up / reset resources here


@pytest.fixture(name="client")
def client_fixture(app):
    return app.test_client()


@pytest.fixture(name="runner")
def runner_fixture(app):
    return app.test_cli_runner()
