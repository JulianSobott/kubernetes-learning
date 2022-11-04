from kubernetes import client, config
import kubernetes.client.rest

from db import db_host
from models import InstanceConfig, Database

CLUSTER_BASE_URL = "k8s.local"


# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()

apps_api = client.AppsV1Api()
core_api = client.CoreV1Api()
networking_api = client.NetworkingV1Api()


def namespace_name(tenant_id: str):
    return f"tenant-{tenant_id}"


def deployment_name(tenant_id: str):
    return f"app-tenant-{tenant_id}"


def deploy_instance(instance: InstanceConfig):
    namespace = namespace_name(instance.tenant_id)
    body = client.V1Namespace()
    body.metadata = client.V1ObjectMeta(name=namespace)
    try:
        core_api.create_namespace(body)
    except kubernetes.client.rest.ApiException as e:
        if e.status == 409:
            pass
        else:
            raise e

    deployment = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(
            name=deployment_name(instance.tenant_id),
            labels={"app": f"tenant-{instance.tenant_id}"},
        ),
        spec=client.V1DeploymentSpec(
            replicas=1,
            selector=client.V1LabelSelector(
                match_labels={"app": f"tenant-{instance.tenant_id}"},
            ),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    labels={"app": f"tenant-{instance.tenant_id}"},
                ),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name=f"app-tenant-{instance.tenant_id}",
                            image="local-registry:35543/example_app:latest",
                            image_pull_policy="Always",
                            ports=[client.V1ContainerPort(container_port=80)],
                            env=[
                                client.V1EnvVar(
                                    name="TENANT",
                                    value=instance.name,
                                ),
                                client.V1EnvVar(
                                    name="DB_USER",
                                    value=instance.db.user,
                                ),
                                client.V1EnvVar(
                                    name="DB_PASSWORD",
                                    value=instance.db.password,
                                ),
                                client.V1EnvVar(
                                    name="DB_HOST",
                                    value=instance.db.host,
                                ),
                                client.V1EnvVar(
                                    name="DB_DATABASE",
                                    value=instance.db.database,
                                ),
                            ],
                        )
                    ]
                ),
            ),
        ),
    )
    try:
        apps_api.create_namespaced_deployment(
            body=deployment,
            namespace=namespace,
        )
    except client.rest.ApiException as e:
        if e.status == 409:
            apps_api.patch_namespaced_deployment(
                name=deployment_name(instance.tenant_id),
                body=deployment,
                namespace=namespace,
            )
        else:
            raise

    service = client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=client.V1ObjectMeta(
            name=deployment_name(instance.tenant_id),
            labels={"app": f"tenant-{instance.tenant_id}"},
        ),
        spec=client.V1ServiceSpec(
            selector={"app": f"tenant-{instance.tenant_id}"},
            ports=[client.V1ServicePort(
                port=8080,
                target_port=80,
            )],
        ),
    )
    try:
        core_api.create_namespaced_service(
            body=service,
            namespace=namespace,
        )
    except client.rest.ApiException as e:
        if e.status == 409:
            core_api.patch_namespaced_service(
                name=deployment_name(instance.tenant_id),
                body=service,
                namespace=namespace,
            )
        else:
            raise

    instance_url = f"{instance.slug}.{CLUSTER_BASE_URL}"
    ingress = client.V1Ingress(
        api_version="networking.k8s.io/v1",
        kind="Ingress",
        metadata=client.V1ObjectMeta(
            name=deployment_name(instance.tenant_id),
            labels={"app": f"tenant-{instance.tenant_id}"},
        ),
        spec=client.V1IngressSpec(
            rules=[
                client.V1IngressRule(
                    host=instance_url,
                    http=client.V1HTTPIngressRuleValue(
                        paths=[
                            client.V1HTTPIngressPath(
                                path="/",
                                path_type="Prefix",
                                backend=client.V1IngressBackend(
                                    service=client.V1IngressServiceBackend(
                                        name=deployment_name(instance.tenant_id),
                                        port=client.V1ServiceBackendPort(
                                            number=8080,
                                        ),
                                    ),
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )
    try:
        networking_api.create_namespaced_ingress(
            body=ingress,
            namespace=namespace,
        )
    except client.rest.ApiException as e:
        if e.status == 409:
            networking_api.patch_namespaced_ingress(
                name=deployment_name(instance.tenant_id),
                body=ingress,
                namespace=namespace,
            )
        else:
            raise
    return f"http://{instance_url}:8081"


def delete_instance(tenant_id: str):
    namespace = namespace_name(tenant_id)
    apps_api.delete_namespaced_deployment(
        name=deployment_name(tenant_id),
        namespace=namespace,
    )
    core_api.delete_namespaced_service(
        name=deployment_name(tenant_id),
        namespace=namespace,
    )
    networking_api.delete_namespaced_ingress(
        name=deployment_name(tenant_id),
        namespace=namespace,
    )
    core_api.delete_namespace(name=namespace)


if __name__ == '__main__':
    deploy_instance(InstanceConfig(
        tenant_id="1",
        name="Test",
        slug="test",
        db=Database(
            user="test",
            password="test",
            host=db_host,
            database="test",
        ),
    ))
