# Variables
DOCKER_USERNAME ?= your-dockerhub-username
VERSION ?= latest

# Image names
FRONTEND_IMAGE = $(DOCKER_USERNAME)/todo-frontend
BACKEND_IMAGE = $(DOCKER_USERNAME)/todo-backend
# DATABASE_IMAGE = $(DOCKER_USERNAME)/todo-postgres

# Default target
.PHONY: all
all: build push

# Build all images
.PHONY: build
build: build-frontend build-backend 

# Push all images
.PHONY: push
push: push-frontend push-backend

# Frontend targets
.PHONY: build-frontend
build-frontend:
	@echo "Building frontend image..."
	docker build -t $(FRONTEND_IMAGE):$(VERSION) -f app/frontend/Dockerfile ./app/frontend

.PHONY: push-frontend
push-frontend:
	@echo "Pushing frontend image..."
	docker push $(FRONTEND_IMAGE):$(VERSION)

# Backend targets
.PHONY: build-backend
build-backend:
	@echo "Building backend image..."
	docker build -t $(BACKEND_IMAGE):$(VERSION) -f app/backend/Dockerfile ./app/backend

.PHONY: push-backend
push-backend:
	@echo "Pushing backend image..."
	docker push $(BACKEND_IMAGE):$(VERSION)

# Database targets
# .PHONY: build-database
# build-database:
# 	@echo "Building database image..."
# 	docker build -t $(DATABASE_IMAGE):$(VERSION) postgres/

# .PHONY: push-database
# push-database:
# 	@echo "Pushing database image..."
# 	docker push $(DATABASE_IMAGE):$(VERSION)

# Login to DockerHub
.PHONY: login
login:
	@echo "Logging in to DockerHub..."
	docker login

# Clean up
.PHONY: clean
clean:
	@echo "Cleaning up images..."
	docker rmi $(FRONTEND_IMAGE):$(VERSION) || true
	docker rmi $(BACKEND_IMAGE):$(VERSION) || true
	# docker rmi $(DATABASE_IMAGE):$(VERSION) || true

# Development commands
.PHONY: dev
dev:
	docker-compose up --build

.PHONY: down
down:
	docker-compose down

# Help target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make all              - Build and push all images"
	@echo "  make build            - Build all Docker images"
	@echo "  make push             - Push all images to DockerHub"
	@echo "  make build-frontend   - Build only frontend image"
	@echo "  make build-backend    - Build only backend image"
	@echo "  make build-database   - Build only database image"
	@echo "  make push-frontend    - Push only frontend image"
	@echo "  make push-backend     - Push only backend image"
	@echo "  make push-database    - Push only database image"
	@echo "  make login            - Login to DockerHub"
	@echo "  make clean            - Remove built images"
	@echo "  make dev              - Run development environment"
	@echo "  make down             - Stop development environment"
	@echo ""
	@echo "Variables:"
	@echo "  DOCKER_USERNAME       - DockerHub username (current: $(DOCKER_USERNAME))"
	@echo "  VERSION              - Image version tag (current: $(VERSION))"