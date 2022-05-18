#!/usr/bin/env python
import json
import os, platform, subprocess, re
import ast
import time
import namespace as namespace
from kubernetes.client import ApiClient, CustomObjectsApi

import time
from Genetic import *
from kubernetes import client, config, watch

config.load_kube_config()  ## From control panel
# config.load_incluster_config()  ### From cluster

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

        time.sleep(120) # To get different mesures after 1 min window
    return cpunode, memnode, cpupods, mempod


def getpodsnb():
    w = watch.Watch()
    S = 0
    for _ in w.stream(v1.list_namespaced_pod, "default", timeout_seconds=1):
        S = S + 1
    return S


####### for tweets we need to change from timer to number of tweets that has be scrapped

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
            if (event['object'].status.container_statuses[0].restart_count != 0) and (
                    event['object'].metadata.name not in info):
                info[event['object'].metadata.name] = {
                    'started_at': event['object'].status.container_statuses[0].last_state.terminated.started_at,
                    'finished_at': event['object'].status.container_statuses[0].last_state.terminated.finished_at
                }
        time.sleep(120)
        print(info)
