FROM ubuntu:latest

ARG USER
ARG APP_PORT
ARG CONTAINER_SRC

ENV APP_PORT=$APP_PORT

ENV CONTAINER_SRC=${CONTAINER_SRC:-/usr/frontend_streamlit}
ENV DATA_DIR=/usr/data
USER $USER
WORKDIR $CONTAINER_SRC

# Create User Home Directory (in case it is needed)
RUN mkdir -p /home/user && chown -R $USER /home/user

# Build Context is services/frontend_streamlit
COPY ./src .
COPY ./docker/requirements.txt ./requirements.txt

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && pip3 install --no-cache-dir --break-system-packages -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="$CONTAINER_SRC:$PATH"

CMD [ "sh", "-c", "streamlit run Game_Time.py --server.port ${APP_PORT}" ]