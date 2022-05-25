import gym
from Kubernetes_Helper import *
from KubeResources import *


## letss start with the tasks cpus's as the state
## selection will be basd on

class CloudEnv(gym.Env):
    def __init__(self,node_dict,tasks,steps):
        """
        Action space : discrite : Genetic, Kube default scheuduler
        Observation space / same state space : we can maybz start with the nb of tasks and their cpu usage and the
        availabe nodes and maybeee later we can alter the nodes resources

        """
        super(CloudEnv, self).__init__()
        self.nodes = node_dict
        self.VMSnumber = len(node_dict)
        self.tasks = tasks
        self.steps = steps

    def step(self, action):
        """
        for each step run one scheduling algo and wait a bit for results and get them and delete pods and restart them
        maybe each time we re-run we run random number of replicas set so that we can vary and change the
        agent's experience
        :param action:
        :return:
        """
        if action == 0:
            algo = 'genetic'
        elif action ==1:
            algo = 'defalu'


        pass

    def reset(self):
        """
        MAYBE WE DO NOT NEED THIIS
        reset the tasks, Deleting all the envi, looking again for availble nodes,
        :return:
        """
        pass

    def termination(self):
        """
        check maybe the number of steps of our agent if we attented that time step we stop
        :return:
        """
        pass

    def reward(self):
        """
        what is our reward function.. this a prob for now
        maybe try one time get the actual mesruements of that cpu of the node
        and on the next
        LATTEEEEER check the condiciton of nodes if one pod got effectied he gets --
        :return:
        """
        pass
