#!/bin/bash

# Default open source core
default_core=free5gc

if [ $# -eq 0 ]; then
  # No arguments provided, use default value
  export CORE_5G=$default_core
  export NAMESPACE=$default_core
  echo Using default core $CORE_5G
else
  # Argument provided, assign it to a variable
  export CORE_5G=$1
  export NAMESPACE=$1
  echo Using $CORE_5G core
fi

# Delete previous existing deployment and service
kubectl delete -n open5gs -f nef-deployment.yaml
#kubectl delete -n $CORE_5G -f nef-deployment.yaml

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
#kubectl apply -n open5gs -f nef-deployment.yaml --env=CORE_5G=$CORE_5G
envsubst < nef-deployment.yaml | kubectl apply -n open5gs -f -
#kubectl apply -n $CORE_5G -f nef-deployment.yaml

# Port forward to service
#kubectl port-forward -n open5gs svc/nef 9000:80
