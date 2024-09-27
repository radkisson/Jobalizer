#!/bin/bash

# Script to build and install the Docker image for the jobalizer application
# Usage:
#   chmod +x build_and_install.sh
#   ./build_and_install.sh [options]
#
# Options:
#   -v          Enable verbose mode
#   -h          Show help message

set -euo pipefail  # Exit on error, undefined variable, or pipe failure

# Variables
IMAGE_NAME="jobalizer"
TEMP_CONTAINER_NAME="jobalizer_temp"
REQUIREMENTS_FILE="requirements.txt"
DEFAULT_IMAGE_TAG="latest"

# Initialize variables
VERBOSE=false
HELP=false

# Function to display usage information
usage() {
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  -v          Enable verbose mode"
  echo "  -h          Show help message"
  exit 0
}

# Function to log messages when verbose mode is enabled
log() {
  if [ "$VERBOSE" = true ]; then
    echo "[INFO] $@"
  fi
}

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to retry a command up to a specified number of times
retry() {
  local retries=$1
  shift
  local count=0

  until "$@"; do
    exit_code=$?
    count=$((count + 1))
    if [ "$count" -lt "$retries" ]; then
      echo "Retry $count/$retries: Command failed with exit code $exit_code. Retrying in 2 seconds..."
      sleep 2
    else
      echo "Error: Command failed after $retries attempts."
      return $exit_code
    fi
  done
}

# Function to clean up dangling Docker images
cleanup_images() {
  log "Cleaning up dangling Docker images..."
  docker image prune -f
}

# Function to clean up unused Docker resources
cleanup_docker_resources() {
  log "Cleaning up unused Docker networks, volumes, and containers..."
  docker network prune -f
  docker volume prune -f
  docker container prune -f
}

# Function to handle cleanup on exit
cleanup_on_exit() {
  log "Performing cleanup before exit..."
  cleanup_images
  cleanup_docker_resources
}

# Trap EXIT to ensure cleanup is done
trap cleanup_on_exit EXIT

# Parse command-line options
while getopts "vh" opt; do
  case $opt in
    v)
      VERBOSE=true
      ;;
    h)
      usage
      ;;
    *)
      usage
      ;;
  esac
done

# Check for required commands (docker)
if ! command_exists docker; then
  echo "Error: Docker is not installed. Please install Docker and try again."
  exit 1
fi

# Check if .env file exists and source it
if [ -f .env ]; then
  log "Sourcing environment variables from .env..."
  # shellcheck disable=SC1091
  source .env
else
  echo "Warning: .env file not found. Using default environment variables."
fi

# Set GENERATE_REQUIREMENTS with default if not set
GENERATE_REQUIREMENTS="${GENERATE_REQUIREMENTS:-false}"

# Set IMAGE_TAG with default or provided value
IMAGE_TAG="${IMAGE_TAG:-$DEFAULT_IMAGE_TAG}"

# Optionally, generate a unique tag using timestamp or Git hash
# Uncomment one of the following lines if desired:
# IMAGE_TAG=$(date +%Y%m%d%H%M%S)
# IMAGE_TAG=$(git rev-parse --short HEAD 2>/dev/null || echo "$DEFAULT_IMAGE_TAG")

log "Building Docker image: $IMAGE_NAME:$IMAGE_TAG with GENERATE_REQUIREMENTS=$GENERATE_REQUIREMENTS"

# Build the Docker image with retry mechanism and custom network settings
retry 3 docker build \
  --network=host \
  --build-arg GENERATE_REQUIREMENTS="$GENERATE_REQUIREMENTS" \
  -t "$IMAGE_NAME:$IMAGE_TAG" \
  .

echo "Docker image '$IMAGE_NAME:$IMAGE_TAG' built successfully."

# Prompt to clean up dangling images
read -r -p "Do you want to clean up dangling Docker images? [y/N]: " cleanup_choice
case "$cleanup_choice" in
  [yY][eE][sS]|[yY])
    cleanup_images
    echo "Dangling Docker images cleaned up."
    ;;
  *)
    echo "Skipping cleanup of dangling Docker images."
    ;;
esac

# Optional: Prompt to clean up unused Docker networks, volumes, and containers
read -r -p "Do you want to clean up unused Docker networks, volumes, and containers? [y/N]: " resource_cleanup_choice
case "$resource_cleanup_choice" in
  [yY][eE][sS]|[yY])
    cleanup_docker_resources
    echo "Unused Docker resources cleaned up."
    ;;
  *)
    echo "Skipping cleanup of Docker resources."
    ;;
esac

# Provide instructions to run the container
echo ""
echo "You can now run the application with the following command:"
echo "  docker run -p 5000:5000 \\"
echo "    -e FLASK_APP=main \\"
echo "    -e FLASK_ENV=${FLASK_ENV:-development} \\"
echo "    -e OPENAI_API_KEY=${OPENAI_API_KEY:-your_openai_api_key} \\"
echo "    -e FLASK_SECRET_KEY=${FLASK_SECRET_KEY:-your_secret_key} \\"
echo "    --env-file .env \\"
echo "    --restart unless-stopped \\"
echo "    $IMAGE_NAME:$IMAGE_TAG"

# Optionally, provide a quick way to run using docker-compose
echo ""
echo "Alternatively, you can use Docker Compose to run the application:"
echo "  docker-compose up -d"
