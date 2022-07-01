"""
Kubernetes Helper functions
"""

from kubernetes import client, config, watch
import time
import random
import os
import numpy as np
import yaml
import subprocess


config.load_kube_config()
v1 = client.CoreV1Api()


def tasks():
    """
    Getting the pending tasks pending waiting to be scheduled
    """
    w = watch.Watch()
    idTask = 0
    taskdict = {}
    replicatset = getreplicatval()
    for event in w.stream(v1.list_namespaced_pod, "default", timeout_seconds=1):
        if event['object'].status.phase == "Pending" and event['object'].status.conditions is None:
            taskdict[idTask] = [event['object'].metadata.name, replicatset[event['object'].metadata.name.split('-')[0]]]
            idTask += 1
    return taskdict


def nodes_available():
    """
    Getting available nodes
    """
    nodes_dict = {}
    counter = 0
    for n in v1.list_node().items:
        for status in n.status.conditions:
            if status.status == "True" and status.type == "Ready":
                nodes_dict[counter] = [n.metadata.name, int(n.status.allocatable['cpu'])]
                counter = counter + 1
    return nodes_dict


def change_scheduler_name(name):
    """
    Changing pod's scheduler name
    :param name: new scheduler name
    """
    tasks = os.listdir('../tasks')
    for i in tasks:
        path = 'tasks/' + i
        with open(path) as file:
            file = yaml.load(file, Loader=yaml.FullLoader)

            file['spec']['template']['spec']['schedulerName'] = name

        with open(path, 'w') as fil:
            documents = yaml.dump(file, fil)


def modify_replicatset():
    """
    Changing the replicat set
    """
    tasks = os.listdir('../tasks')
    for i in tasks:
        path = 'tasks/' + i
        with open(path) as file:
            file = yaml.load(file, Loader=yaml.FullLoader)
            file['spec']['template']['spec']['val'] = random.randint(1, 4)

        with open(path, 'w') as fil:
            documents = yaml.dump(file, fil)


def delete_pods():
    """
    Deleting pods
    """
    bashCommand = "kubectl delete -f tasks/."
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    result = process.communicate()
    while pods_nb("Running") != 0:
        time.sleep(2)


def apply_pods():
    """
    Applying pods
    :return:
    """
    bashCommand = "kubectl apply -f tasks/. --validate=false"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    result = process.communicate()
    time.sleep(2)


def reset(new_epi):
    """

    :param new_epi: boolean that specifying if we are resting inside an episode
    :return: Array containing the number of available machines and tasks to be scheduled
    """
    delete_pods()
    change_scheduler_name('waiting')
    if new_epi:
        modify_replicatset()
        time.sleep(1)
    apply_pods()
    return np.array([pods_nb('Pending'), len(nodes_available())])


def apply_changes():
    delete_pods()
    apply_pods()


def reconfigure(name):
    change_scheduler_name(name)
    apply_changes()


def getlist(dic):
    L = []
    for i in dic:
        L.append(dic[i][-1])
    return L


def pods_nb(status):
    w = watch.Watch()
    S = 0
    for event in w.stream(v1.list_namespaced_pod, "default", timeout_seconds=1):
        if event['object'].status.phase == status and 'round' not in event['object'].metadata.name:
            S = S + 1
    return S


def getreplicatval():
    taskslist = os.listdir('../tasks')
    values = {}
    for i in taskslist:
        path = 'tasks/' + i
        with open(path) as file:
            file = yaml.load(file, Loader=yaml.FullLoader)
            values[file['metadata']['name']] = file['spec']['template']['spec']['val']

    return values


def avg(dic):
    for i in dic:
        dic[i] = sum(dic[i]) / len(dic[i])
    L = []
    for i in dic:
        L.append(dic[i])
    return L


def get_nextstate():
    return [0, len(nodes_available())]


def avg_time(dic):
    S = 0
    for i in dic:
        S = S + (dic[i].total_seconds())
    return S
