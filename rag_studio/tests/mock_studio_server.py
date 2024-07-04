from unittest.mock import MagicMock
import rag_studio.studio_webserver as ws


def create_app():
    return ws.create_app(
        config={"REPO_NAME": "rag-studio-scratch-repo"}, model_builder=MagicMock()
    )
