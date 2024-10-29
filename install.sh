#!/bin/bash

# Default values
default_name=nef
default_core=free5gc
default_plmn="'20899'"
prune=false

# Iterate through the arguments
for arg in "$@"; do
  if [ "$arg" = "-p" ]; then
    prune=true
    break
  fi
done

export NAME=$default_name
echo Deploying $NAME

if [ $# -eq 0 ]; then
  export CORE_5G=$default_core
  export NAMESPACE=$default_core
  export PLMN=$default_plmn
  echo Deploying along with $CORE_5G in default namespace: $NAMESPACE in default PLMN: $PLMN
if [ $# -eq 1 ]; then
  export CORE_5G=$1
  export NAMESPACE=$1
  export PLMN=$default_plmn
  echo Deploying along with $CORE_5G in default namespace: $NAMESPACE in default PLMN: $PLMN
if [ $# -eq 2 ]; then
  export CORE_5G=$1
  export NAMESPACE=$2
  export PLMN=$default_plmn
  echo Deploying along with $CORE_5G in namespace: $NAMESPACE in default PLMN: $PLMN
if [ $# -eq 3 ]; then
  export CORE_5G=$1
  export NAMESPACE=$2
  export PLMN=$3
  echo Deploying along with $CORE_5G in namespace: $NAMESPACE in PLMN: $PLMN
# else
#   export CORE_5G=$1
#   export PLMN=$default_plmn
#   if [ -n "$2" ]; then
#     export NAMESPACE=$2
#   else
#     export NAMESPACE=$1
#   fi
#   echo Deploying along with $CORE_5G core in namespace: $NAMESPACE in default PLMN: $PLMN
# fi

# Delete previous existing deployment and service
# kubectl delete -n $NAMESPACE -f nef-deployment.yaml
envsubst < nef-deployment.yaml | kubectl delete -n $NAMESPACE -f -

# Deploy the app to Kubernetes
envsubst < nef-deployment.yaml | kubectl apply -n $NAMESPACE -f -
