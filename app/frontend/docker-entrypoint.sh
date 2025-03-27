#!/bin/bash
set -e

# Set default value for BACKEND_URL if not provided
BACKEND_URL=${BACKEND_URL:-http://backend:8000}
echo "Using backend URL: $BACKEND_URL"

# Replace placeholders in the nginx template
envsubst '${BACKEND_URL}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# Execute the CMD from the Dockerfile
exec "$@"
