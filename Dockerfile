# syntax=docker/dockerfile:1

# Use a build argument to specify the base image tag
ARG BASE_IMAGE_TAG=latest
FROM byronthomas712/trial-container:${BASE_IMAGE_TAG}

# Set the working directory in the container
WORKDIR /app

# Copy all Python files from the build context, excluding those in the 'tests' directory
COPY --chown=root:root ./rag_studio/*.py /app/rag_studio/

ENV VLLM_DO_NOT_TRACK=1
# ENTRYPOINT ["fastapi" "run" "rag_studio/inference_webserver.py"]
ENTRYPOINT ["bash", "-c", "service ssh start; source ~/.profile && flask --app rag_studio.webserver run --debug --no-reload --host=0.0.0.0"]