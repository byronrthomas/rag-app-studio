# Rag Studio

## Design choices

### Inference endpoints

Our inference endpoint is API-compatible with OpenAI's APIs for chat and legacy completions. We kept the API
the same as this is likely to make integrating with clients (including ThetaEdge cloud's own UI) easier.

### Evaluation (QA)

Although we recognise that the ability to evaluate an LLM application built using RAGStudio is important,
most evaluation methods rely on asking a "Gold-standard" LLM model to check the quality of the responses
coming from the LLM application. Given that a core rationale behind using RAGStudio with local models is
to not send prompts or contextual documents to outside services like OpenAI, this form of evaluating a model
doesn't fully make sense as our only options for the "Gold-standard local LLM" are:

1. Use the LLM being used for inference - this is unlikely to give fair evaluations in most cases, since a single model will be checking it's own responses
2. Use a "bigger LLM" model that's running locally - although this is a possibility, it means that all use cases need to specify two models, where one is trusted more - in many cases the user would probably want to use this "better" model for their actual inference rather than a less good one

Given this, we decided to only initially support two forms of evaluation:

1. Use user-specified pairs of test query and ideal responses, and check the "semantic similarity" of the application's response to the query vs the user-specified "ideal response"
2. Use the inference LLM to work out whether the document retrieval is working well - the LLM has not been used for this part of the process, so it can fairly be asked whether some document chunk is relevant to a user's query

## Developer instructions

### Install deps

This project was developed with Python 3.11.8 and is not currently intended to be supported for other versions.
We recommend using a tool like `pyenv` with `virtualenv` (or something equivalent like conda/poetry) to install specific python
versions and to keep libraries in use for different projects isolated from each other.

To install deps needed to run without a GPU run:

`pip install -r requirements-cpu.txt`

### Needs huggingFace access token

In order to run any tests or run the server locally, you must have an access token that can write to a repo, and
tell huggingface about it using `huggingface-cli login`

### Build a new tag

```
docker build --build-arg BASE_IMAGE_TAG=2.2 -t byronthomas712/trial-container:2.2-prod-start .
```

### Run from tag

```
docker run -d -p 5000:5000 --rm --name theta-container-trial byronthomas712/trial-container:0.1 --bind-all
```
