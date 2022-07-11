from algos.Genetic import *
from kubernetes import client, config
from utils.Kubernetes_Helper import nodes_available, tasks

config.load_kube_config()  ## hedhi tekhdm ki nlansi mn hnee
v1 = client.CoreV1Api()

scheduler_name = "genetic"


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
    time_matrix = [[round(t / p, 3) for p in processors] for t in tasks]
    carac = Setup(len(taskdict), len(nodes_dict), time_matrix)
    gts = GeneticTaskScheduler()
    gts.schedule(carac)
    best = gts.best_of_all
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


def schedule():
    taskdict = tasks()
    nodes_dict = nodes_available()
    schduled = genetic(nodes_dict, taskdict)
    for i in taskdict:
        scheduler(taskdict[i][0], match(i, schduled, nodes_dict)[0])

# def main():
#     schedule()
#     _, met = resources()
#     return met
