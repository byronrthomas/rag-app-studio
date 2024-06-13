# Trial container

## Build a new tag

```
docker build -t byronthomas712/trial-container:0.1 .
```

## Run from tag

```
docker run -d -p 5000:5000 --rm --name theta-container-trial byronthomas712/trial-container:0.1 --bind-all
```
