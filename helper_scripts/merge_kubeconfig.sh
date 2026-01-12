#!/bin/sh

# Usage: ./script.sh
# This script is merging a kubeconfig file to another one

tmp='_kubeconfig.yaml.tmp'
kubeconfig='_kubeconfig.yaml'
dir='kubeconfig/'

for file in $(ls kubeconfig/ | grep 'kubeconfig.yaml'); do
    file="$dir/$file"
    export KUBECONFIG="./$file:./$kubeconfig"

    kubectl config view --flatten > $tmp
    cp $tmp $kubeconfig
    rm $tmp
done

cat $kubeconfig

exit