#!/bin/bash

# Find and delete the Docker image by name
IMAGE_ID=$(docker images -q nef)
docker rmi -f $IMAGE_ID

# Pull the latest changes from Git
git pull

# Build the new Docker image
docker build -t nef .

# Tag the image and push it to the repository
docker tag nef:latest jacintoluf/nef:v1
docker push jacintoluf/nef:v1

# Deploy the app to Kubernetes
kubectl apply -n open5gs -f dummy-nef-deployment.yml
