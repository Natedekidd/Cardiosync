IMAGE_NAME  := cardiosync-ai
API_PORT    := 8000
DOCKER_PORT := 8000

.PHONY: help install api docker-build docker-run docker-stop docker-logs health health-docker

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Local:"
	@echo "  install       Install dependencies (uv sync)"
	@echo "  api           Start FastAPI server on port $(API_PORT)"
	@echo "  health        Health check on local API"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build  Build Docker image"
	@echo "  docker-run    Run container on port $(DOCKER_PORT)"
	@echo "  docker-stop   Stop and remove container"
	@echo "  docker-logs   Stream container logs"
	@echo "  health-docker Health check on Docker container"

install:
	uv sync

api:
	uv run uvicorn src.api:app --host 0.0.0.0 --port $(API_PORT) --reload

docker-build:
	docker build -t $(IMAGE_NAME) .

docker-run:
	docker run -d --name $(IMAGE_NAME) -p $(DOCKER_PORT):80 $(IMAGE_NAME)

docker-stop:
	docker stop $(IMAGE_NAME) && docker rm $(IMAGE_NAME)

docker-logs:
	docker logs -f $(IMAGE_NAME)

health:
	curl -s http://localhost:$(API_PORT)/health | python3 -m json.tool

health-docker:
	curl -s http://localhost:$(DOCKER_PORT)/health | python3 -m json.tool
