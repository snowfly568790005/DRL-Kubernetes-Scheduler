import time
import random

import yaml
import subprocess

from kubernetes.watch import watch

from utils.KubeResources import v1


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
    time.sleep(40)  ## wating for tasks to be deleted
    bashCommand = "kubectl apply -f tasks/. --validate=false"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    result = process.communicate()


def update(name):
    change_sched(name)
    apply_changes()


def wait(state): ## could be terminating
    w = watch.Watch()
    for event in w.stream(v1.list_namespaced_pod, "default", timeout_seconds=1):
        pass
        ## break until its clear
        print(event)


def modify_replicatset():
    for i in tasks:
        path = 'tasks/' + i
        with open(path) as file:
            file = yaml.load(file, Loader=yaml.FullLoader)
            file['spec']['replicas'] = random.randint(1,5)
            file['spec']['template']['spec']['val'] = random.randint(1,4)


        with open(path, 'w') as fil:
            documents = yaml.dump(file, fil)

random.randint(1,)