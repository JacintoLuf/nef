#!/bin/bash

# Delete previous existing deployment and service
kubectl delete deployment -n open5gs nef
kubectl delete service -n open5gs nef
kubectl delete clusterrole -n open5gs nef-services-read
kubectl delete clusterrolebinding -n open5gs nef-services-read-rb
kubectl delete serviceaccount -n open5gs nef-account

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
kubectl apply -n open5gs -f nef-deployment.yml

# Port forward to service
#kubectl port-forward -n open5gs svc/nef 9000:80
