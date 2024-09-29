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
DEFAULT_IMAGE_TAG="latest"

# Initialize variables
VERBOSE=true

# Prompt to generate requirements.txt
read -p "Do you want to generate a new requirements.txt (GENERATE_REQUIREMENTS=true)? [y/N]: " gen_req && [[ "$gen_req" =~ ^[yY]$ ]] && GENERATE_REQUIREMENTS=true || GENERATE_REQUIREMENTS=false

# Function to display usage information
usage() {
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  -v          Enable verbose mode"
  echo "  -h          Show this help message"
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

# Output Docker version
log "Docker Version: $(docker --version)"

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

# Set IMAGE_TAG with default or provided value
IMAGE_TAG="${IMAGE_TAG:-$DEFAULT_IMAGE_TAG}"

# Function for conditional cleanup prompts
cleanup_prompt() {
  local prompt=$1
  local action=$2
  if [ "$VERBOSE" = true ]; then
    $action
  else
    read -r -p "$prompt [y/N]: " choice
    case "$choice" in
      [yY][eE][sS]|[yY])
        $action
        ;;
      *)
        echo "Skipping $prompt."
        ;;
    esac
  fi
}

# Build the Docker image
log "Building Docker image: $IMAGE_NAME:$IMAGE_TAG"
retry 3 docker build \
  -t "$IMAGE_NAME:$IMAGE_TAG" \
  .

echo "Docker image '$IMAGE_NAME:$IMAGE_TAG' built successfully."

# If GENERATE_REQUIREMENTS is true, generate requirements.txt
if [ "$GENERATE_REQUIREMENTS" = true ]; then
  log "Generating requirements.txt from the Docker image..."
  
  # Create a temporary container
  temp_container=$(docker create "$IMAGE_NAME:$IMAGE_TAG")
  
  # Copy requirements.txt from the container to the host
  docker cp "$temp_container:/app/requirements.txt" ./requirements.txt
  
  echo "Updated requirements.txt has been copied to the host."
  
  # Remove the temporary container
  docker rm "$temp_container"
fi

# Prompt to clean up dangling images
cleanup_prompt "Do you want to clean up dangling Docker images?" cleanup_images

# Optional: Prompt to clean up unused Docker networks, volumes, and containers
cleanup_prompt "Do you want to clean up unused Docker networks, volumes, and containers?" cleanup_docker_resources

# Provide instructions to run the container
echo ""
echo "You can now run the application with the following command:"
echo "  docker run -p 5000:5000 \\"
echo "    -e FLASK_APP=app \\"
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
