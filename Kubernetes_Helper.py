#!/usr/bin/env python

import ast
import yaml
import subprocess

from kubernetes import client, config, watch

config.load_kube_config()
v1 = client.CoreV1Api()


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
    Getting the tasks on pending waiting for scheduling
    :return:
    """
    w = watch.Watch()
    idTask = 0
    taskdict = {}
    for event in w.stream(v1.list_namespaced_pod, "default", timeout_seconds=1):
        if event['object'].status.phase == "Pending" and event['object'].status.conditions is None and \
                event['object'].spec.scheduler_name == 'waiting':
            taskdict[idTask] = [event['object'].metadata.name, ast.literal_eval(
                event['object'].metadata.annotations['kubectl.kubernetes.io/last-applied-configuration'])['spec'][
                'val']]
            idTask += 1
    return taskdict


def change_sched(name):
    tasks = ['calcul300.yaml', 'calcul400.yaml', 'calcul500.yaml', 'calcul600.yaml']
    for i in tasks:
        path = 'tasks/' + i
        with open(path) as file:
            file = yaml.load(file, Loader=yaml.FullLoader)
            file['spec']['schedulerName'] = name
        print(file)

        with open(path, 'w') as fil:
            print(file)
            documents = yaml.dump(file, fil)


def apply_changes():
    bashCommand = "kubectl delete -f tasks/."
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    result = process.communicate()
    print(result)
    bashCommand = "kubectl apply -f tasks/. --validate=false"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    result = process.communicate()
    print(result)


def reconfigure(name):
    change_sched(name)
    apply_changes()
