# syntax=docker/dockerfile:1

# Use a build argument to specify the base image tag
ARG BASE_IMAGE_TAG=latest
FROM byronthomas712/trial-container:${BASE_IMAGE_TAG}

# Set the working directory in the container
WORKDIR /app

# Copy all Python files from the build context, excluding those in the 'tests' directory
COPY --chown=root:root ./rag_studio/*.py /app/rag_studio/
COPY --chown=root:root ./rag_studio/evaluation/*.py /app/rag_studio/evaluation/
COPY --chown=root:root ./rag_studio/inference/*.py /app/rag_studio/inference/
# Also copy the builder_static assets to be served statically
COPY --chown=root:root ./rag_studio/builder_static /app/rag_studio/builder_static

ENV VLLM_DO_NOT_TRACK=1
ENV VLLM_CONFIGURE_LOGGING=0
ENTRYPOINT ["bash", "-c", "service ssh start; source ~/.profile && flask --app rag_studio.studio_webserver run --no-reload --host=0.0.0.0 --port=8000"]