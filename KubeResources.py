#!/usr/bin/env python
from datetime import time

from kubernetes.client import CustomObjectsApi

from kubernetes import client, config, watch

config.load_kube_config()  ## From control panel

v1 = client.CoreV1Api()


def used_resources():
    """
    Getting 3 measurements of cpu and memory usage in pods and nodes in 1 one-minute window
    """
    cust = CustomObjectsApi()
    nodes = cust.list_cluster_custom_object('metrics.k8s.io', 'v1beta1', 'nodes')
    pods = cust.list_cluster_custom_object('metrics.k8s.io', 'v1beta1', 'namespaces/default/pods')
    cpupods = {}
    mempod = {}
    cpunode = {}
    memnode = {}
    for t in range(3):
        for i in nodes['items']:
            if i['metadata']['name'] not in cpunode:
                cpunode[i['metadata']['name']] = [i['usage']['cpu']]
                memnode[i['metadata']['name']] = [i['usage']['memory']]
            else:
                cpunode[i['metadata']['name']].append(i['usage']['cpu'])
                memnode[i['metadata']['name']].append(i['usage']['memory'])

        for i in pods['items']:
            if i['metadata']['name'] not in cpupods:
                cpupods[i['metadata']['name']] = [i['containers'][0]['usage']['cpu']]
                mempod[i['metadata']['name']] = [i['containers'][0]['usage']['memory']]
            else:
                cpupods[i['metadata']['name']].append(i['containers'][0]['usage']['cpu'])
                mempod[i['metadata']['name']].append(i['containers'][0]['usage']['memory'])

        time.sleep(35)  # To get different mesures after 10s  window
    return cpunode, memnode, cpupods, mempod


def getpodsnb():
    w = watch.Watch()
    S = 0
    for event in w.stream(v1.list_namespaced_pod, "default", timeout_seconds=1):
        if event['object'].status.phase == "Running":
            S = S + 1
    return S


def exec_time():
    """
    Finding the execution time of each pod once it has finished
    :return:
    """
    nb = getpodsnb()
    w = watch.Watch()
    info = {}
    while nb != len(info):
        for event in w.stream(v1.list_namespaced_pod, "default", timeout_seconds=1):
            if (event['object'].status.container_statuses is not None and (
                    event['object'].status.container_statuses[0].restart_count != 0)
                    and (event['object'].metadata.name not in info)):
                info[event['object'].metadata.name] = {
                    'Scheduler': event['object'].spec.scheduler_name,
                    'started_at': event['object'].status.container_statuses[0].last_state.terminated.started_at,
                    'finished_at': event['object'].status.container_statuses[0].last_state.terminated.finished_at
                }
        time.sleep(10)
    return info


def results():
    print('current running pods ', getpodsnb())
    cpunode, memnode, cpupods, mempod = used_resources()
    print('CPU and Memory used in NODES')
    print(cpunode)
    print(memnode)
    print('CPU and Memory used in PODS')
    print(cpupods)
    print(mempod)
    print('Total execution time ')
    print(exec_time())
