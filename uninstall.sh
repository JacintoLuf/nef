#!/bin/bash

default_name=nef
default_core=free5gc
default_plmn="'20899'"
prune=false

export NAME=$default_name
echo Deleting $NAME

if [ $# -eq 0 ]; then
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
envsubst < nef-deployment.yaml | kubectl delete -n $NAMESPACE -f -