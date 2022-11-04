from kubernetes import client, config
import kubernetes.client.rest

from db import db_host, db_database_name, db_user_name, db_password
from models import Database, InstanceBaseConfig, InstanceSetupConfig

CLUSTER_BASE_URL = "k8s.local"
DB_CONNECTION_SECRET_NAME = "database-connection"
CONFIG_MAP_NAME = "app-config"


# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()

apps_api = client.AppsV1Api()
core_api = client.CoreV1Api()
networking_api = client.NetworkingV1Api()


def namespace_name(tenant_id: str):
    return f"tenant-{tenant_id}"


def deployment_name(tenant_id: str):
    return f"app-tenant-{tenant_id}"


def first_deployment(instance: InstanceSetupConfig):
    namespace = namespace_name(instance.tenant_id)

    # create namespace
    body = client.V1Namespace()
    body.metadata = client.V1ObjectMeta(name=namespace)
    core_api.create_namespace(body)

    # create secrets
    database = instance.db.database
    user = instance.db.user
    password = instance.db.password
    database_secret = client.V1Secret(
        metadata=client.V1ObjectMeta(
            name=DB_CONNECTION_SECRET_NAME,
            namespace=namespace,
        ),
        string_data={
            "host": db_host,
            "database": database,
            "user": user,
            "password": password,
        },
    )
    core_api.create_namespaced_secret(namespace, database_secret)

    # create configmap
    configmap = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(
            name=CONFIG_MAP_NAME,
            namespace=namespace,
        ),
        data={
            "TENANT_NAME": instance.name,
            "TENANT_SLUG": instance.slug,
            "TENANT_ID": instance.tenant_id,
        },
    )
    core_api.create_namespaced_config_map(namespace, configmap)


def deploy_instance(instance: InstanceBaseConfig):
    namespace = namespace_name(instance.tenant_id)

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
                            image=f"local-registry:35543/example_app:{instance.version}",
                            ports=[client.V1ContainerPort(container_port=80)],
                            env=[
                                client.V1EnvVar(
                                    name="TENANT",
                                    value_from=client.V1EnvVarSource(
                                        config_map_key_ref=client.V1ConfigMapKeySelector(
                                            name=CONFIG_MAP_NAME,
                                            key="TENANT_NAME",
                                        ),
                                    ),
                                ),
                                client.V1EnvVar(
                                    name="DB_USER",
                                    value_from=client.V1EnvVarSource(
                                        secret_key_ref=client.V1SecretKeySelector(
                                            name=DB_CONNECTION_SECRET_NAME,
                                            key="user",
                                        ),
                                    )
                                ),
                                client.V1EnvVar(
                                    name="DB_PASSWORD",
                                    value_from=client.V1EnvVarSource(
                                        secret_key_ref=client.V1SecretKeySelector(
                                            name=DB_CONNECTION_SECRET_NAME,
                                            key="password",
                                        ),
                                    )
                                ),
                                client.V1EnvVar(
                                    name="DB_HOST",
                                    value_from=client.V1EnvVarSource(
                                        secret_key_ref=client.V1SecretKeySelector(
                                            name=DB_CONNECTION_SECRET_NAME,
                                            key="host",
                                        ),
                                    )
                                ),
                                client.V1EnvVar(
                                    name="DB_DATABASE",
                                    value_from=client.V1EnvVarSource(
                                        secret_key_ref=client.V1SecretKeySelector(
                                            name=DB_CONNECTION_SECRET_NAME,
                                            key="database",
                                        ),
                                    )
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

    slug = core_api.read_namespaced_config_map(
        name=CONFIG_MAP_NAME,
        namespace=namespace,
    ).data["TENANT_SLUG"]
    instance_url = f"{slug}.{CLUSTER_BASE_URL}"
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
