#!/bin/bash

'''
Do the following to build and install the dependencies:
    chmod +x build_and_install.sh
    ./build_and_install.sh
'''

set -e  # Exit immediately if a command exits with a non-zero status
set -u  # Treat unset variables as an error

IMAGE_NAME="jobalizer"
TEMP_CONTAINER_NAME="jobalizer_temp"
REQUIREMENTS_FILE="requirements.txt"

#!/bin/bash

IMAGE_NAME="jobalizer"

# Check if .env file exists and source it
if [ -f .env ]; then
  source .env
else
  echo "Warning: .env file not found. Using default environment variables."
fi

# Build the Docker image, passing GENERATE_REQUIREMENTS as a build argument
docker build --build-arg GENERATE_REQUIREMENTS="${GENERATE_REQUIREMENTS:-false}" -t $IMAGE_NAME .

echo "Done. Now you can run the application with 'docker run -p 80:80 $IMAGE_NAME'."