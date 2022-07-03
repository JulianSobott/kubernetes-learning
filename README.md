# Learning kubernetes


## Example Fast API app

### Using cmd
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

### Using deployment file

```shell
# WORKDIR kubernetes/example_app

kubectl apply -f example-app-deployment.yaml

# Deploy new image
kubectl rollout restart deployment/example-app-deployment
```

### Pod to pod communication

```shell
# WORKDIR kubernetes/example_multi_services

# prepare docker images
docker build service_01 -t firstcluster-registry:41703/service_01:latest
docker build service_02 -t firstcluster-registry:41703/service_02:latest
docker push firstcluster-registry:41703/service_01:lates
docker push firstcluster-registry:41703/service_02:lates

# start services
kubectl apply -f service_01/service-01-deployment.yaml
kubectl apply -f service_02/service-02-deployment.yaml

# check if it is working

curl http://$(kubectl get svc | grep service-02 | awk '{ print $4}'):8080
```
