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
    # pods = cust.list_cluster_custom_object('metrics.k8s.io', 'v1beta1', 'namespaces/default/pods')
    # cpupods = {}
    # mempod = {}
    cpunode = {}
    memnode = {}
    for t in range(3):
        for i in nodes['items']:
            if i['metadata']['name'] not in cpunode:
                cpunode[i['metadata']['name']] = [int(i['usage']['cpu'][:len(i['usage']['cpu']) - 1])]
                memnode[i['metadata']['name']] = [int(i['usage']['memory'][:len(i['usage']['memory']) - 2])]
            else:
                cpunode[i['metadata']['name']].append(int(i['usage']['cpu'][:len(i['usage']['cpu']) - 1]))
                memnode[i['metadata']['name']].append(int(i['usage']['memory'][:len(i['usage']['memory']) - 2]))

        # for i in pods['items']:
        #     if i['metadata']['name'] not in cpupods:
        #         cpupods[i['metadata']['name']] = [
        #             int(i['containers'][0]['usage']['cpu'][:len(i['containers'][0]['usage']['cpu']) - 1])]
        #         mempod[i['metadata']['name']] = [
        #             int(i['containers'][0]['usage']['memory'][:len(i['containers'][0]['usage']['memory']) - 2])]
        #     else:
        #         cpupods[i['metadata']['name']].append(
        #             int(i['containers'][0]['usage']['cpu'][:len(i['containers'][0]['usage']['cpu']) - 1]))
        #         mempod[i['metadata']['name']].append(
        #             int(i['containers'][0]['usage']['memory'][:len(i['containers'][0]['usage']['memory']) - 2]))

        # time.sleep(35)  # To get different mesures after 10s  window

    return final(cpunode), final(memnode)  # , final(cpupods), final(mempod)


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
        # time.sleep(10)
    for i in info:
        info[i] = info[i]['finished_at'] - info[i]['started_at']
    return info


def final(dic):
    for i in dic:
        dic[i] = sum(dic[i]) / len(dic[i])
    return dic


def printresults():
    print('current running pods ', getpodsnb())
    cpunode, memnode=  used_resources()
    print('CPU and Memory used in NODES')
    print(cpunode)
    print(memnode)
    print('Total execution time ')
    print(exec_time())


def resources():
    cpunode, memnode = used_resources()
    return cpunode, memnode, exec_time()


def metric():
    cpunode, memnode = used_resources()
    S = 0
    for i in cpunode:
        Avg = (cpunode[i] + memnode[i]) / 2
        S = ((Avg - cpunode[i]) ** 2) / 2 + ((Avg - memnode[i]) ** 2) / 2
    return S / len(cpunode) , exec_time()


# print(resources())
print(metric())
