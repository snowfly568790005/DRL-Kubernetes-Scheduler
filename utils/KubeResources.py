#!/usr/bin/env python
import time as t

from kubernetes.client import CustomObjectsApi
from utils.Kubernetes_Helper import *

config.load_kube_config()  # From control panel

v1 = client.CoreV1Api()


def used_resources():
    """
    Getting 3  measurements of cpu and memory usage in pods and nodes in 1 one-minute window to calculate the average
    resource utilisation
    :return: avg(cpu_node) : Average CPU utilisation in the cluster
             avg(mem_node) : Average Memory in the cluster
    """

    # pods = cust.list_cluster_custom_object('metrics.k8s.io', 'v1beta1', 'namespaces/default/pods')
    # cpu_pods = {}
    # mem_pod = {}
    cpu_node = {}
    mem_node = {}
    for _ in range(3):
        cust = CustomObjectsApi()
        nodes = cust.list_cluster_custom_object('metrics.k8s.io', 'v1beta1', 'nodes')
        for i in nodes['items']:
            if i['metadata']['name'] not in cpu_node:
                cpu_node[i['metadata']['name']] = [int(i['usage']['cpu'][:len(i['usage']['cpu']) - 1])]
                mem_node[i['metadata']['name']] = [int(i['usage']['memory'][:len(i['usage']['memory']) - 2])]
            else:
                try:
                    cpu_node[i['metadata']['name']].append(int(i['usage']['cpu'][:len(i['usage']['cpu']) - 1]))
                    mem_node[i['metadata']['name']].append(int(i['usage']['memory'][:len(i['usage']['memory']) - 2]))
                except ValueError:
                    print('bad value')
                    print(i['usage']['cpu'][:len(i['usage']['cpu']) - 1])
        time.sleep(10)

        # for i in pods['items']:
        #     if i['metadata']['name'] not in cpu_pods:
        #         cpu_pods[i['metadata']['name']] = [
        #             int(i['containers'][0]['usage']['cpu'][:len(i['containers'][0]['usage']['cpu']) - 1])]
        #         mem_pod[i['metadata']['name']] = [
        #             int(i['containers'][0]['usage']['memory'][:len(i['containers'][0]['usage']['memory']) - 2])]
        #     else:
        #         cpu_pods[i['metadata']['name']].append(
        #             int(i['containers'][0]['usage']['cpu'][:len(i['containers'][0]['usage']['cpu']) - 1]))
        #         mem_pod[i['metadata']['name']].append(
        #             int(i['containers'][0]['usage']['memory'][:len(i['containers'][0]['usage']['memory']) - 2]))

        # time.sleep(35)  # To get different mesures after 10s  window

    return avg(cpu_node), avg(mem_node)  # , final(cpu_pods), final(mem_pod)


def exec_time():
    """
    Getting the execution time of each pod once finished
    :return: info : Dictionary containing the pod name, and it's execution time
    """
    w = watch.Watch()
    info = {}
    while True:
        for event in w.stream(v1.list_namespaced_pod, "default", timeout_seconds=1):
            if 'round' not in event['object'].metadata.name:
                if (event['object'].status.container_statuses is not None and (
                        event['object'].status.container_statuses[0].restart_count != 0)
                        and (event['object'].metadata.name not in info)
                        and ('round' not in event['object'].metadata.name)):
                    if event['object'].status.container_statuses[0].last_state.terminated is not None:
                        time_used = (event['object'].status.container_statuses[0].last_state.terminated.finished_at -
                                     event['object'].status.container_statuses[0].last_state.terminated.started_at)
                        info[event['object'].metadata.name] = time_used
                    else:
                        continue
        stop = True
        for event in w.stream(v1.list_namespaced_pod, "default", timeout_seconds=1):
            if event['object'].status.container_statuses[0].last_state.terminated is None:
                stop = False
        if stop:
            break
        t.sleep(10)
    return info


def resources():
    """
    Getting all the studied resources
    :return: List of  the cluster's average execution time and  imbalance degree
    """
    cpu_node, mem_node = used_resources()
    execution_time = avg_time(exec_time())
    imbalan_deg = imbalance_degree(cpu_node, mem_node)
    return [execution_time, imbalan_deg]
    #return imbalan_deg


def imbalance_degree(cpu_node, mem_node):
    S = 0
    for i in range(len(cpu_node)):
        Avg = (cpu_node[i] + mem_node[i]) / 2
        S = ((Avg - cpu_node[i]) ** 2) / 2 + ((Avg - mem_node[i]) ** 2) / 2
    return S / len(cpu_node)
