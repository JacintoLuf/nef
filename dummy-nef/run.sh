#!/bin/bash

# Default open source core
default_core=free5gc
default_plmn=20899
prune=false

# Iterate through the arguments
for arg in "$@"; do
  if [ "$arg" = "-dp" ]; then
    prune=true
    break
  fi
done

if [ $# -eq 0 ]; then
  export CORE_5G=$default_core
  export NAMESPACE=$default_core
  export PLMN=$default_plmn
  echo Using default core $CORE_5G in default namespace: $NAMESPACE in default PLMN: $PLMN
else
  export CORE_5G=$1
  export PLMN=$default_plmn
  if [ -n "$2" ]; then
    export NAMESPACE=$2
  else
    export NAMESPACE=$1
  fi
  echo Using $CORE_5G core in namespace: $NAMESPACE in default PLMN: $PLMN
fi

# Delete previous existing deployment and service
kubectl delete -n $NAMESPACE -f nef-deployment.yaml
#kubectl delete -n $CORE_5G -f nef-deployment.yaml

# Find and delete the local Docker image by name
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
docker tag nef:latest jacintoluf/nef:$CORE_5G
docker push jacintoluf/nef:$CORE_5G

if [ "$prune" = true ]; then
  docker system prune
fi

# Deploy the app to Kubernetes
#kubectl apply -n open5gs -f nef-deployment.yaml --env=CORE_5G=$CORE_5G
envsubst < nef-deployment.yaml | kubectl apply -n $NAMESPACE -f -
