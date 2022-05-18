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

config.load_kube_config()  ## hedhi tekhdm ki nlansi mn hnee
# config.load_incluster_config()  ### hedhii for kuber cluster

v1 = client.CoreV1Api()

scheduler_name = "genetic"


def nodes_available():
    nodes_dict = {}
    counter = 0
    for n in v1.list_node().items:
        for status in n.status.conditions:
            if status.status == "True" and status.type == "Ready":
                nodes_dict[counter] = [n.metadata.name, int(n.status.allocatable['cpu'])]
                counter = counter + 1
    return nodes_dict


def scheduler(name, node, namespace="default"):
    """
    The affecting  function after Scheduling
    :param name:
    :param node:
    :param namespace:
    :return:
    """
    target = client.V1ObjectReference()
    target.kind = "Node"
    target.apiVersion = "v1"
    target.name = node
    meta = client.V1ObjectMeta()
    meta.name = name
    body = client.V1Binding(target=target)
    body.metadata = meta
    print(name, 'scheduled by', node)
    return v1.create_namespaced_binding(namespace, body, _preload_content=False)


def genetic(nodes_dict, taskdict):
    """
    Genetic Scheduler
    :param nodes_dict:
    :param taskdict:
    :return:
    """
    tasks = [taskdict[i][-1] for i in taskdict]
    processors = [nodes_dict[i][-1] for i in nodes_dict]
    print(processors)
    time_matrix = [[round(t / p, 3) for p in processors] for t in tasks]
    carac = Setup(len(taskdict), len(nodes_dict), time_matrix)
    gts = GeneticTaskScheduler()
    gts.schedule(carac)
    best = gts.best_of_all
    print(best)
    return best


def match(i, sched, nodes_dict):
    """
    Matches the pod index to it's affected node name to schdule
    :param i:
    :param sched:
    :param nodes_dict:
    :return:
    """
    return nodes_dict[sched[i]]


def tasks():
    """
    Getting the tasks on pending waiting for Genetic scheduler
    :return:
    """
    w = watch.Watch()
    idTask = 0
    taskdict = {}
    for event in w.stream(v1.list_namespaced_pod, "default", timeout_seconds=1):
        if event['object'].status.phase == "Pending" and event['object'].status.conditions is None and \
                event['object'].spec.scheduler_name == scheduler_name:
            taskdict[idTask] = [event['object'].metadata.name, ast.literal_eval(
                event['object'].metadata.annotations['kubectl.kubernetes.io/last-applied-configuration'])['spec'][
                'val']]
            idTask += 1
    return taskdict


def main():
    print(v1.list_namespaced_pod)
    print('Nodes :', nodes_available())
    taskdict = tasks()
    nodes_dict = nodes_available()
    schduled = genetic(nodes_dict, taskdict)
    print(taskdict)
    for i in taskdict:
        scheduler(taskdict[i][0], match(i, schduled, nodes_dict)[0])


if __name__ == '__main__':
    main()
