from datetime import datetime
import sys
from flask import Flask, jsonify, request, redirect
from flask_cors import CORS


def create_app(test_config=None):
    app = Flask(__name__)
    CORS(app)

    # Capture the current time
    startTime = datetime.now()

    @app.route("/")
    def hello_world():
        return jsonify({"message": "Hello, World!"})

    @app.route("/healthcheck")
    def healthcheck_api():
        """Healthcheck API to check if the API is running."""
        return jsonify(
            {
                "message": "API is running!",
                "start_time": startTime.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    @app.route("/upload", methods=["POST"])
    def upload_file_api():
        if "file" not in request.files:
            return jsonify({"message": "No file part in the request"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"message": "No file selected for uploading"}), 400
        if file:
            file.save(file.filename)
            return jsonify({"message": "File uploaded successfully"}), 200

    @app.route("/files")
    def list_files_api():
        return jsonify({"message": "List of files"})

    @app.route("/trycompletion", methods=["POST"])
    def try_completion_api():
        return jsonify({"message": "Try completion"})

    @app.route("/checkpoint", methods=["POST"])
    def checkpoint_api():
        return jsonify({"message": "Checkpoint"})

    @app.route("/inference-container-details", methods=["POST"])
    def inference_container_details_api():
        return jsonify({"message": "Inference container details"})

    return app
