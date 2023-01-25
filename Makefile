.DEFAULT_GOAL := app
.PHONY := app build run rm rebuild

CONTAINER_NAME := arzontop
DOCKER_VOLUME := "/var/www"

app: Dockerfile
	@docker exec -it $(CONTAINER_NAME) sh
build: Dockerfile
	@docker build -t $(CONTAINER_NAME) .
run: Dockerfile
	@docker run --name $(CONTAINER_NAME) -v $(PWD):$(DOCKER_VOLUME) -d $(CONTAINER_NAME):latest
rm: Dockerfile
	@docker rm -f $(CONTAINER_NAME)
rebuild: Dockerfile build rm run app
