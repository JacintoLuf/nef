#!/bin/bash

# Delete previous existing deployment and service
kubectl delete -n open5gs -f nef-deployment.yaml
#kubectl delete deployment -n open5gs nef
#kubectl delete service -n open5gs nef
# Uncomment on first run
#kubectl delete clusterrole pods-list
#kubectl delete clusterrolebinding pods-list
#kubectl delete serviceaccount -n open5gs nef-account

# Find and delete the Docker image by name
IMAGE_ID=$(docker images -q nef)
if [ ! -z "$IMAGE_ID" ]; then
  echo $IMAGE_ID
  docker rmi -f $IMAGE_ID
fi