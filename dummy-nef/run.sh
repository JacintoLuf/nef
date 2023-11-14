#!/bin/bash

# Default open source core
default_core=free5gc

if [ $# -eq 0 ]; then
  # No arguments provided, use default value
  export 5G_CORE=$default_core
  echo Using default core $5G_CORE
else
  # Argument provided, assign it to a variable
  export 5G_CORE=$1
  echo Using $5G_CORE core
fi

# Delete previous existing deployment and service
kubectl delete -n open5gs -f nef-deployment.yaml
#kubectl delete -n $5g_core -f nef-deployment.yaml

# Find and delete the Docker image by name
IMAGE_ID=$(docker images -q nef)
if [ ! -z "$IMAGE_ID" ]; then
  echo $IMAGE_ID
  docker rmi -f $IMAGE_ID
fi

# Pull the latest changes from Git
git pull

# Build the new Docker image
docker build -t nef .

# Tag the image and push it to the repository
docker tag nef:latest jacintoluf/nef:v1
docker push jacintoluf/nef:v1

# Deploy the app to Kubernetes
#kubectl apply -n open5gs -f nef-deployment.yaml --env=5G_CORE=$5G_CORE
envsubst < nef-deployment.yaml | kubectl apply -n open5gs -f -
#kubectl apply -n $5G_CORE -f nef-deployment.yaml

# Port forward to service
#kubectl port-forward -n open5gs svc/nef 9000:80
