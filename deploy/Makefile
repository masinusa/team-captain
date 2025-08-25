SHELL := /bin/bash



export CURRENT_UID=$(id -u):$(id -g)
include local.env
export

deploy_local:
	@echo "Backend API: http://localhost:${BACKEND_PORT}/docs"
	@echo "Frontend Streamlit: http://localhost:${FRONTEND_PORT}"
	@docker compose -f ./local.docker-compose.yaml \
		--env-file local.env \
		up 
	
	
# cloud_deployment:
# 	...


################
# Dev Targets #
################

rebuild:
	docker compose -f ./local.docker-compose.yaml \
		--env-file local.env \
		build

rebuild-no-cache:
	docker compose -f ./local.docker-compose.yaml \
		--env-file local.env \
		build --no-cache

enter-backend-container:
	docker compose -f ./local.docker-compose.yaml \
		--env-file local.env \
		run --rm local_backend_tc bash

enter-frontend-st-container:
	docker compose -f ./local.docker-compose.yaml \
		--env-file local.env \
		run --rm local_web_streamlit_tc bash