import json
import sys
from flask import Flask, jsonify, request, redirect
from flask_cors import CORS
from datetime import datetime

api = Flask(__name__)
CORS(api)

# Capture the current time
startTime = datetime.now()


def check_args():
    opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
    args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]

    KNOWN_OPTS = {"--bind-all": "bind-all"}
    rejected = args
    rejected.extend([r for r in opts if r not in KNOWN_OPTS])
    if len(rejected):
        raise SystemExit(f"Usage: {sys.argv[0]} {' '.join(KNOWN_OPTS.keys())}...")
    return {KNOWN_OPTS[k]: k in opts for k in KNOWN_OPTS}


@api.route("/")
def hello_world():
    return jsonify({"message": "Hello, World!"})


@api.route("/healthcheck")
def healthcheck():
    return jsonify(
        {
            "message": "API is running!",
            "start_time": startTime.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )


def main(bind_all_addresses=False):
    if bind_all_addresses:
        api.run(host="0.0.0.0")
    else:
        api.run()


if __name__ == "__main__":
    args = check_args()
    main(args["bind-all"])
