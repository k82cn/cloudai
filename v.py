from kubernetes import config, client
from kubernetes.dynamic import DynamicClient

from kubernetes.client import V1PodList

# Load the kubeconfig file from the default location (~/.kube/config)
config.load_kube_config()

# Create a dynamic client
dyn_client = DynamicClient(client.ApiClient())
api_instance = client.CoreV1Api()

job_resource = dyn_client.resources.get(api_version='batch.volcano.sh/v1alpha1', kind='Job')
queue_resource = dyn_client.resources.get(api_version='scheduling.volcano.sh/v1beta1', kind='Queue')

def create_node_group(client, name, node_list):
    for node in node_list:
        body = {
            "metadata": {
                "labels": { "cloudai/node-group": name }
            }
        }

        client.patch_node(node, body)

def create_queue(client, name, node_group):
    queue_spec = {
        'apiVersion': 'scheduling.volcano.sh/v1beta1',
        'kind': 'Queue',
        'metadata': {
            'name': name,
            'namespace': 'default'
        },
        'spec': {
            'affinity': {
                'nodeGroupAffinity': {
                    'requiredDuringSchedulingIgnoredDuringExecution':  ['cloudai/node-group=' + node_group]
                }
            }
        }
    }

    client.create(body=queue_spec, namespace='default')

def delete_queue(client, name):
    client.delete(name=name)

def run_job(client, name, queue_name, tasks):
    # Calculate from tasks.replicas
    min_available = 3
    job_spec = {
        'apiVersion': 'batch.volcano.sh/v1alpha1',
        'kind': 'Job',
        'metadata': {
            'name': name,
            'namespace': 'default'
        },
        'spec': {
            'minAvailable': min_available,
            'schedulerName': 'volcano',
            'maxRetry': 3,
            'queue': queue_name,
            'tasks': tasks
        }
    }

    client.create(body=job_spec, namespace='default')

def delete_job(client, ns, name):
    client.delete(name=name, namespace=ns)

def list_job(client):
    return client.get(namespace='default')

queue_1 = 'queue-1'
group_1 = 'group-1'
group_1_nodes = ['swx-forge02']

create_node_group(api_instance, group_1, group_1_nodes)

create_queue(queue_resource, queue_1, group_1)

tasks = [
    {
        'replicas': 6,
        'name': 'default-nginx',
        'template': {
            'metadata': {
                'name': 'web'
            },
            'spec': {
                'containers': [
                    {
                        'image': 'nginx',
                        'imagePullPolicy': 'IfNotPresent',
                        'name': 'nginx',
                        'resources': {
                            'requests': {
                                'cpu': '1'
                            }
                        }
                    }
                ]
            }
        }
    }
]

run_job(job_resource, 'job-1', queue_1, tasks)

jobs = list_job(job_resource)

for job in jobs.items:
    print(f"Name: {job.metadata.name}, Namespace: {job.metadata.namespace}\n")

# Delete all jobs
# for job in jobs.items:
#     delete_job(job_resource, job.metadata.namespace, job.metadata.name)

# Delete queue
# delete_queue(queue_resource, queue_1)

# TODO(k82cn): delete node group

