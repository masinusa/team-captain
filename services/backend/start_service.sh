
gunicorn --workers 4 --max-requests 150 --chdir $CONTAINER_BACKEND_SRC main:app --bind 0.0.0.0:$BACKEND_PORT --backlog 2048 --timeout $BACKEND_TIMEOUT --worker-class uvicorn.workers.UvicornWorker