# Quick config guide

## Install
* install kubectl https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/
* install az cli https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-linux?view=azure-cli-latest&pivots=apt
* install snap https://snapcraft.io/docs/installing-snap-on-debian
* sudo snap install kubelogin
* sudo az aks install-cli

## Connect
* Fill _kubeconfig file from existing kubeconfig file from another computer (ask to Devops team if needed)
  > Tips: ./create_acces_and_kubeconfig.sh is intended to create a global reader service account on the kubernetes cluster
* test:
  * kubectl config get-contexts
  * kubectl config use-context CONTEXT
  * kubectl config get-contexts
  * kubectl get ns --kubeconfig _kubeconfig


## How to pull image from ghcr.io
* export CR_PAT=YOUR_TOKEN
* echo $CR_PAT | docker login ghcr.io -u USER --password-stdin


## Trigger a manual inventory from docker
* docker restart apiventory-apiventory-1