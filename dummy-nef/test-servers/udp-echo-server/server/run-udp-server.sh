#!/bin/bash

# Delete previous existing deployment and service
kubectl delete deployment -n open5gs udp-echo-server
kubectl delete service -n open5gs udp-echo-server
kubectl delete deployment -n open5gs udp-echo-server2
kubectl delete service -n open5gs udp-echo-server2

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
docker tag nef:latest jacintoluf/nef:udp
docker push jacintoluf/nef:udp

# Deploy the app to Kubernetes
kubectl apply -n open5gs -f udp-server-deployment.yaml
kubectl apply -n open5gs -f udp-server2-deployment.yaml

# Port forward to service
#kubectl port-forward -n open5gs svc/nef 9000:80
