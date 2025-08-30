FROM ubuntu:latest

ARG USER
ARG APP_PORT
ARG CONTAINER_SRC
ARG GUNICORN_WORKERS
ARG GUNICORN_TIMEOUT
ARG GUNICORN_BACKLOG
ARG GUNICORN_MAX_REQUESTS

ENV APP_PORT=$APP_PORT
ENV GUNICORN_WORKERS=$GUNICORN_WORKERS
ENV GUNICORN_TIMEOUT=$GUNICORN_TIMEOUT
ENV GUNICORN_BACKLOG=$GUNICORN_BACKLOG
ENV GUNICORN_MAX_REQUESTS=$GUNICORN_MAX_REQUESTS

ENV CONTAINER_SRC=${CONTAINER_SRC:-/usr/backend}
USER $USER
WORKDIR $CONTAINER_SRC

# Create User Home Directory (in case it is needed)
RUN mkdir -p /home/user && chown -R $USER /home/user

# Build Context 
COPY ./src .
COPY ./docker/requirements.txt ./requirements.txt

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && pip3 install --no-cache-dir --break-system-packages -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="$CONTAINER_SRC:$PATH"

CMD [ "sh", "-c", \
    "gunicorn \
    --workers $GUNICORN_WORKERS \
    --max-requests $GUNICORN_MAX_REQUESTS \
    --chdir $CONTAINER_SRC \
    --bind 0.0.0.0:$APP_PORT \
    --backlog $GUNICORN_BACKLOG \
    --timeout $GUNICORN_TIMEOUT \
    --worker-class uvicorn.workers.UvicornWorker \
    --reload \
    backend_main:app" \
]