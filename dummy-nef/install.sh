#!/bin/bash

# Default values
default_name=nef
default_core=free5gc
default_plmn=20899
prune=false

# Iterate through the arguments
for arg in "$@"; do
  if [ "$arg" = "-p" ]; then
    prune=true
    break
  fi
done

if [ $# -eq 0 ]; then
  export NAME=$default_name
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

# Deploy the app to Kubernetes
envsubst < nef-deployment.yaml | kubectl apply -n $NAMESPACE -f -
