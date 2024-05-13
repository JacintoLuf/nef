#!/bin/bash

default_name=nef
default_core=free5gc
default_plmn="'20899'"
prune=false

if [ $# -eq 0 ]; then
  export NAME=$default_name
  export CORE_5G=$default_core
  export NAMESPACE=$default_core
  export PLMN=$default_plmn
  echo Deleting $NAME in default namespace: $NAMESPACE with default PLMN: $PLMN
else
  export CORE_5G=$1
  export PLMN=$default_plmn
  if [ -n "$2" ]; then
    export NAMESPACE=$2
  else
    export NAMESPACE=$1
  fi
  echo Deleting $NAME in namespace: $NAMESPACE with default PLMN: $PLMN
fi

# Delete previous existing deployment and service
kubectl delete -n $NAMESPACE -f nef-deployment.yaml

# Find and delete the Docker image by name
IMAGE_ID=$(docker images -q nef)
if [ ! -z "$IMAGE_ID" ]; then
  echo $IMAGE_ID
  docker rmi -f $IMAGE_ID
fi