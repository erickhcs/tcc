#!/usr/bin/env python

import time
import random
import json
from kubernetes import client, config, watch

config.load_kube_config(config_file='/etc/kubernetes/admin.conf')
v1=client.CoreV1Api()

scheduler_name = "vrscheduler"

def nodes_available():
    ready_nodes = []
    for n in v1.list_node().items:
            for status in n.status.conditions:
                if status.status == "True" and status.type == "Ready":
                    ready_nodes.append(n.metadata.name)
    return ready_nodes

def scheduler(pod_name, node_name, namespace="default"):
    metadata = client.V1ObjectMeta(name=pod_name)
    target = client.V1ObjectReference(
            kind="Node",
            api_version="v1",
            name=node_name
        )
    
    body = client.V1Binding(metadata=metadata,target=target)

    try:
        res = v1.create_namespaced_binding(namespace, body)
        if res:
            print(f"POD: {pod_name} scheduled and place on node {node_name}") 
    except Exception as a:
        print("Exception when calling CoreV1Api->create_namespaced_binding: %s\n" % a)
        pass

def main():
    print("SCHEDULER STARTED")
    w = watch.Watch()
    for event in w.stream(v1.list_namespaced_pod, namespace="default"):
        print(f"EVENT: {event['type']}; {event['object'].kind}; {event['object'].status.phase}; {event['object'].metadata.name}; {event['object'].spec.scheduler_name}")
        print(f"RESULT: {event['object'].status.phase == 'Pending' and event['object'].spec.scheduler_name == scheduler_name}") 
        if event['object'].status.phase == "Pending" and event['object'].spec.scheduler_name == scheduler_name:
            try:
                nodes = nodes_available()
                if not nodes:
                    print("No available nodes.")
                    continue
                selectedNode = random.choice(nodes)
                print(selectedNode)
                res = scheduler(event['object'].metadata.name, selectedNode)
                print(f"Scheduled pod {event['object'].metadata.name} on node {selectedNode}.")
            except client.rest.ApiException as e:
                print (json.loads(e.body)['message'])
                pass

if __name__ == '__main__':
    main()
