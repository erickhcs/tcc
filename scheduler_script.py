#!/usr/bin/env python

import time
import random
import json
import threading
import os

from kubernetes import client, config, watch

config.load_kube_config(config_file='/etc/kubernetes/admin.conf')
v1=client.CoreV1Api()

delay_thresold = 50
nodes = ['worker1.vrk8s2.ilabt-imec-be.wall2.ilabt.iminds.be', 'worker2.vrk8s2.ilabt-imec-be.wall2.ilabt.iminds.be', 'worker3.vrk8s2.ilabt-imec-be.wall2.ilabt.iminds.be']
scheduler_name = "vrscheduler"
nodes_delay = [85, 70, 34]
isSchedulerActive = False

def scheduler(pod_name, node_name, namespace="default"):
    metadata = client.V1ObjectMeta(name=pod_name)
    target = client.V1ObjectReference(
            kind="Node",
            api_version="v1",
            name=node_name
        )
    
    body = client.V1Binding(metadata=metadata,target=target)

    try:
        res = v1.create_namespaced_binding(namespace=namespace, body=body)
        if res:
            print(f"POD: {pod_name} scheduled and place on node {node_name}") 
    except Exception as a:
        print("Exception when calling CoreV1Api->create_namespaced_binding: %s\n" % a)
        pass

def activate_scheduler_after_one_minute():
    global isSchedulerActive
    time.sleep(60)
    isSchedulerActive = True
    print('SCHEDULER ACTIVATED: ', isSchedulerActive)

def get_good_nodes():
    good_nodes = []

    for index, value in enumerate(nodes_delay):
        if value <= delay_thresold:
            good_nodes.append(nodes[index])

    return good_nodes

def get_bad_nodes():
    bad_nodes = []

    for index, value in enumerate(nodes_delay):
        if value > delay_thresold:
            bad_nodes.append(nodes[index])

    return bad_nodes

def delete_pod_from_bad_node(bad_nodes, pod_name, current_node_name):
    global isSchedulerActive
    
    if isSchedulerActive == False:
        return

    if current_node_name in bad_nodes:
        os.system('export KUBECONFIG=/etc/kubernetes/admin.conf')
        os.system(f'kubectl delete pods {pod_name}')
        print(f'Pod {pod_name} has been deleted from node {current_node_name}!')
    
def main():
    print("SCHEDULER STARTED")

    global isSchedulerActive
    thread = threading.Thread(target=activate_scheduler_after_one_minute)
    thread.start()

    w = watch.Watch()

    good_nodes = get_good_nodes()
    bad_nodes = get_bad_nodes()

    print("GOOD NODES: ", good_nodes)
    print("BAD NODES: ", bad_nodes)

    for event in w.stream(v1.list_namespaced_pod, namespace="default"):
        current_pod = event['object']

        print(f"EVENT: {event['type']}; {current_pod.kind}; {current_pod.status.phase}; {current_pod.metadata.name}; {current_pod.spec.scheduler_name}")
        print(f"RESULT: {current_pod.status.phase == 'Pending' and current_pod.spec.scheduler_name == scheduler_name}") 
        
        delete_pod_from_bad_node(bad_nodes, current_pod.metadata.name, current_pod.spec.node_name)

        if current_pod.status.phase == "Pending" and current_pod.spec.scheduler_name == scheduler_name:
            try:
                if isSchedulerActive == False:
                    selectedNode = random.choice(nodes)
                else:
                    if len(good_nodes) == 0:
                        continue
                    else:
                        selectedNode = random.choice(good_nodes)
                res = scheduler(current_pod.metadata.name, selectedNode)
                print(f"Scheduled pod {current_pod.metadata.name} on node {selectedNode}.")
            except client.rest.ApiException as e:
                print (json.loads(e.body)['message'])
                pass

if __name__ == '__main__':
    main()
