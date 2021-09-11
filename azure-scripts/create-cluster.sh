#!/bin/bash

# Variables
resourceGroup="acdnd-c4-project"
clusterName="udacity-cluster"
region="westeurope"
myAcrName="myacr202106"

# Install aks cli
echo "Installing AKS CLI"

az aks install-cli

echo "AKS CLI installed"

# Create AKS cluster
echo "Step 1 - Creating AKS cluster $clusterName"
# Use either one of the "az aks create" commands below
# For users working in their personal Azure account
# This commmand will not work for the Cloud Lab users, because you are not allowed to create Log Analytics workspace for monitoring
az aks create \
    --resource-group $resourceGroup \
    --name $clusterName \
    --node-count 1 \
    --enable-addons monitoring \
    --generate-ssh-keys \
    --location $region \
    --attach-acr $myAcrName

# For Cloud Lab users
# az aks create \
#     --resource-group $resourceGroup \
#     --name $clusterName \
#     --node-count 1 \
#     --generate-ssh-keys

# For Cloud Lab users
# This command will is a substitute for "--enable-addons monitoring" option in the "az aks create"
# Use the log analytics workspace - Resource ID
# For Cloud Lab users, go to the existing Log Analytics workspace --> Properties --> Resource ID. Copy it and use in the command below.
#az aks enable-addons -a monitoring -n $clusterName -g $resourceGroup --workspace-resource-id "/subscriptions/6c39f60b-2bb1-4e37-ad64-faaf30beaca4/resourcegroups/cloud-demo-153430/providers/microsoft.operationalinsights/workspaces/loganalytics-153430"

echo "AKS cluster created: $clusterName"

# Connect to AKS cluster

echo "Step 2 - Getting AKS credentials"

az aks get-credentials \
    --resource-group $resourceGroup \
    --name $clusterName \
    --verbose

echo "Verifying connection to $clusterName"

kubectl get nodes

echo "Deploying to AKS cluster"
The command below will deploy a standard application to your AKS cluster.
kubectl apply -f ../azure-vote-all-in-one-redis.yaml
# Test the application at the External IP
# It will take a few minutes to come alive.
#kubectl get service azure-vote-front --watch
# You can also verify that the service is running like this
#kubectl get service
# Check the status of each node
#kubectl get pods
# Push your local changes to the remote Github repo, preferably in the Deploy_to_AKS branch

#Create an autoscaler by using the following Azure CLI command
#kubectl autoscale deployment azure-vote-front --cpu-percent=70 --min=1 --max=10


##Now, to generate the synthetic load on the AKS cluster, you can run:

# Generate load in the terminal by creating a container with "busybox" image
# Open the bash into the container
#kubectl run -it --rm load-generator --image=busybox /bin/sh
#You will see a new command prompt. Enter the following in the new command prompt. It will send an infinite loop of queries to the cluster and increase the load on the cluster.

#while true; do wget -q -O- 20.93.199.149; done