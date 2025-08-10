FROM ubuntu:latest

ARG USER
ARG CONTAINER_SRC
ARG APP_PORT
ARG GUNICORN_WORKERS
ARG GUNICORN_TIMEOUT
ARG GUNICORN_BACKLOG
ARG GUNICORN_MAX_REQUESTS

USER $USER
WORKDIR $CONTAINER_SRC

# Build Context is services/backend
COPY ./src .
COPY ./docker/requirements.txt ./requirements.txt

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && pip3 install --no-cache-dir -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*

CMD [ \
    "sh", \
    "-c", \
    "gunicorn", \
    "--workers", "$GUNICORN_WORKERS", \
    "--max-requests", "$GUNICORN_MAX_REQUESTS", \
    "--chdir", "$CONTAINER_SRC", \
    "main:app", \
    "--bind", "0.0.0.0:$APP_PORT", \
    "--backlog", "$GUNICORN_BACKLOG", \
    "--timeout", "$GUNICORN_TIMEOUT", \
    "--worker-class", "uvicorn.workers.UvicornWorker" \
]