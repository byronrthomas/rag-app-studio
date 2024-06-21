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
