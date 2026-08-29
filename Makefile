SHELL := /bin/bash

FRONTEND_PORT ?= 8081

run:
	@echo "Team Captain (web): http://localhost:${FRONTEND_PORT}"
	@cd frontend/src && streamlit run Game_Time.py --server.port ${FRONTEND_PORT}

install:
	pip install -r frontend/docker/requirements.txt

docker-build:
	docker build -t team_captain_web -f frontend/docker/Dockerfile frontend \
		--build-arg USER=$(shell id -u):$(shell id -g) \
		--build-arg APP_PORT=${FRONTEND_PORT} \
		--build-arg CONTAINER_SRC=/usr/frontend_streamlit

docker-run:
	docker run --rm -p ${FRONTEND_PORT}:${FRONTEND_PORT} \
		-v $(CURDIR)/frontend/data:/usr/data \
		team_captain_web
