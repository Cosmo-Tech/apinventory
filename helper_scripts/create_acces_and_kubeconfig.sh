#!/bin/sh

# Usage: set the context of the right cluster, then just ./script.sh
# /!\ it works on current active context, and an admin access is needed
# This script is creating access for apinventory, including:
#  - a service account
#  - a clusterrole (global reader (including secrets), no write access)
#  - a clusterrolebinding
#  - a secret containing a token (that is to connect used from kubectl)
#
# -> Then a local kubeconfig file is created, intended to be merged to an existing kubeconfig file (with ./merge_kubeconfig.sh)


# Variables
CONTEXT="$(kubectl config current-context)"
SA_NAME="cosmo-apinventory-$CONTEXT"
ROLE_NAME="cosmo-apinventory-global-reader"
NAMESPACE="default"
KUBECONFIG_DIR=kubeconfig
KUBECONFIG_FILE="$KUBECONFIG_DIR/$CONTEXT.kubeconfig.yaml"

mkdir -p $KUBECONFIG_DIR

# Create service account
kubectl create serviceaccount $SA_NAME -n $NAMESPACE

# Create custom role to be able to read everything on cluster (default 'view' role is not enough because we need to read secrets)
kubectl apply -f - <<EOF
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: $ROLE_NAME
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
- nonResourceURLs: ["*"]
  verbs: ["get"]
EOF

# Create cluster role binding with the custom role
kubectl create clusterrolebinding $SA_NAME-binding --clusterrole=$ROLE_NAME --serviceaccount=$NAMESPACE:$SA_NAME

# Save token in a secret
kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: $SA_NAME-secret
  namespace: $NAMESPACE
  annotations:
    kubernetes.io/service-account.name: $SA_NAME
type: kubernetes.io/service-account-token
EOF


TOKEN="$(kubectl get secret $SA_NAME-secret -n $NAMESPACE -o json | jq -r '.data.token' | base64 --decode)"
CA_CERT="$(kubectl get secret $SA_NAME-secret -n $NAMESPACE -o json | jq -r '.data."ca.crt"')"
SERVER_URL="$(kubectl config view --minify -o json | jq -r '.clusters[0].cluster.server')"

echo $TOKEN
echo $CA_CERT
echo $SERVER_URL

# Generate a kube config structure
echo "apiVersion: v1
kind: Config
clusters:
- name: $CONTEXT
  cluster:
    certificate-authority-data: $CA_CERT
    server: $SERVER_URL
contexts:
- name: $CONTEXT
  context:
    cluster: $CONTEXT
    namespace: $NAMESPACE
    user: $SA_NAME
current-context: $CONTEXT
users:
- name: $SA_NAME
  user:
    token: $TOKEN" > $KUBECONFIG_FILE


# export KUBECONFIG=./$KUBECONFIG_FILE:./_kubeconfig.yaml
# kubectl config view --flatten > _kubeconfig.yaml.tmp
# cp _kubeconfig.yaml.tmp _kubeconfig.yaml
# rm _kubeconfig.yaml.tmp
# cat _kubeconfig.yaml

echo ''
ls | grep "$CONTEXT" | grep 'kubeconfig.yaml'



exit