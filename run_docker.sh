#!/bin/bash

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker daemon is not running. Please start Docker Desktop or the docker service."
  exit 1
fi

# Check for .env file
if [ ! -f .env ]; then
  echo "Creating .env from .env.example..."
  cp .env.example .env
  echo "Please edit .env to add your API keys before running."
fi

# Build and Run
echo "Building and starting the application..."
docker-compose up --build
