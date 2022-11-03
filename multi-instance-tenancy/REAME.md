# Multi-instance tenancy

Deploy one application multiple times for different tenants.

## setup

Kubernetes Cluster with local registry is required.
See: https://k3d.io/v5.4.3/usage/registries/#using-a-local-registry

```shell
# create cluster
k3d cluster create --registry-create local-registry -p "8081:80@loadbalancer" saas-01

# set hosts dns
echo "\
127.0.0.1   tenant1.k8s.local
127.0.0.1   tenant2.k8s.local
127.0.0.1   k8s.local" | sudo tee --append /etc/hosts

# get registry port
REGISTRY_PORT=$(docker port local-registry 5000/tcp | sed "s/0.0.0.0://")

# WORKDIR multi-instance-tenancy/app
# build and push image
docker build . -t example_app -t local-registry:$REGISTRY_PORT/example_app:latest
docker push local-registry:$REGISTRY_PORT/example_app:latest
```

## Deploy

```shell
kubectl apply -f deployment-1.yaml --namespace=tenant1
kubectl apply -f deployment-2.yaml --namespace=tenant2
```

## Test

```shell
curl http://tenant1.k8s.local:8081
curl http://tenant2.k8s.local:8081
```
