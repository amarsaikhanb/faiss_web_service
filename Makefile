.PHONY: build run test
.DEFAULT_GOAL := build

DOCKER_IMAGE := ba0jy/faiss_web_service

# FAISS_VERSION := $(shell curl -s https://api.github.com/repos/facebookresearch/faiss/releases/latest | jq -r .tag_name | cut -c2-)
# faiss releases info always not updated
FAISS_VERSION := 1.6.0

build:
	docker build \
		--tag $(DOCKER_IMAGE):$(FAISS_VERSION)-cpu \
		--tag $(DOCKER_IMAGE):latest .
		#--build-arg IMAGE=ba0jy/faiss_docker:$(FAISS_VERSION)-cpu \

run:
	docker run \
		-d \
		--rm \
		--tty \
		--interactive \
		--publish 5000:5000 \
		$(DOCKER_IMAGE) $*
		#--volume $(PWD):/opt/faiss_web_service \

test:
	docker run \
		--rm \
		--tty \
		--interactive \
		--entrypoint bash \
		$(DOCKER_IMAGE) -c "python3 -m unittest discover"
		#--volume $(PWD):/opt/faiss_web_service \
