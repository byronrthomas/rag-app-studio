# Trial container

## Build a new tag

```
docker build -t byronthomas712/trial-container:0.1 .
```

## Run from tag

```
docker run -d -p 5000:5000 --rm --name theta-container-trial byronthomas712/trial-container:0.1 --bind-all
```

### NOTES on DigitalOcean bits

cd /tmp/trial1/
python3 -m local_embeddings_trial

docker run -it --rm --network=host -v /root/trial1:/tmp/trial1 --cpuset-cpus=0 --cpuset-mems=0 vllm-cpu-env

# First version that actually did something helpful was a 16GB

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
