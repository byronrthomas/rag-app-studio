# RAG App Studio Frontend

This is the frontend code for RAG App Studio.

It is built using Vite, ReactJS and Tailwind CSS.

## Env vars

Using Vite's normal env var processing, we have non-secret variables stored in `.env.development` - used when
we are running the frontend locally in the dev server, and also in `.env.production` - which is incorporated
into the assets built into the containers.

The only var we have is an API prefix. In production, our python webserver serves pre-built frontend assets
statically, so the API prefix can be nothing - the frontend running at 
`https://theta-edge-cloud-sever-whatever/index.html` is free to just request using a relative `/api/data` for example
and the request goes to the correct place - the same webserver.

In dev, we will be running the frontend at `http://localhost:5173`, so we typically need to direct the API requests
to either `http://localhost:8000` or similar or some `https://theta-edge-cloud-sever-whatever` that is our
model deployment in the cloud.

**IMPORTANT**: the API prefix should not end in '/' - for consistency the frontend code checks this and won't
start if it's set, you can just take it off and leave the rest of the prefix. 
A prefix of '' is fine - this is what production uses.

## Two builds

Because this project has two distinct frontend apps & two distinct containers - a builder and runner, this Vite
project also has two builds, selected between using two vite configs. They share common code under the `common`
folder (public assets are also here), but they each have their own specific code under `apps/builder` and `apps/runner`