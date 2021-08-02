from kubernetes import client, config
from time import sleep
import os
import json

JOB_NAME = "sleep-job"
NAMESPACE = "default"

def main():

    if os.getenv('PRODUCTION') == 'True':
        print("Get configuration from service account")
        config.load_incluster_config()
    else:
        print("Get configuration from kube-config file")
        config.load_kube_config()

    v1 = client.CoreV1Api()
    batch = client.BatchV1Api()

    print("1. CREATE A JOB")
    container = client.V1Container(
        name="sleeper",
        image="busybox",
        command=["sleep", "5000"])
    podTemplate = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"owner": "0gis0"}),
        spec=client.V1PodSpec(containers=[container], restart_policy="Never"))
    jobSpec = client.V1JobSpec(
        template=podTemplate,
        backoff_limit=4)
    job = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(name=JOB_NAME),
        spec=jobSpec)

    response = batch.create_namespaced_job(namespace=NAMESPACE, body=job)
    print(f"Job created. Let's wait until is ready")

    sleep(1)

    print("2. LIST PODS with label owner=gis")
    response = v1.list_namespaced_pod(
        namespace=NAMESPACE, label_selector="owner=0gis0")

    # iterate over all pods
    for pod in response.items:
        print(f"{pod.metadata.name}")

    print("3. DELETE JOB")
    response = batch.delete_namespaced_job(
        name="sleep-job", namespace=NAMESPACE, body=client.V1DeleteOptions(propagation_policy="Foreground", grace_period_seconds=5))
    print(f"Job deleted. status='{response.status}'")

    print("4. LIST SECRETS")
    try:
        response = v1.list_namespaced_secret(namespace=NAMESPACE)
        for secret in response.items:
            print(f"{secret.metadata.name}")
    except Exception as e:
        jsonEx = json.loads(e.body)
        message = jsonEx["message"]
        print(f"Exception: {message}")


if __name__ == "__main__":
    main()