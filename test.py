import datetime
import time
import random

import yaml
import subprocess


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


def test():
    print(random.random())

# Terminating

dic = {'calcul300': datetime.timedelta(seconds=300), 'calcul400': datetime.timedelta(seconds=400), 'calcul500': datetime.timedelta(seconds=500), 'calcul600': datetime.timedelta(seconds=600)}
S = 0
for i in dic:
    S = S + (dic[i].total_seconds())
print(S / len(dic))