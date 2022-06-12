# Learning kubernetes


## Example Fast API app

```shell
# WORKDIR kubernetes/example_app

# prepare docker image
docker build . -t example_app
docker tag example_app:latest firstcluster-registry:41703/example_app:latest

# upload docker image using local registry
# see: https://k3d.io/v5.4.3/usage/registries/#using-a-local-registry
# don't forget to set /etc/hosts
docker push firstcluster-registry:41703/example_app:latest

# run app
kubectl run --image firstcluster-registry:41703/example_app:latest --port 80 example-app
kubectl get pods

# expose service
kubectl expose pod example-app --type=LoadBalancer --port=8080 --target-port=80
kubectl get services
```