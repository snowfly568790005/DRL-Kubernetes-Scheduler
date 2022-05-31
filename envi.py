import collections
import time
import numpy as np

import gym
from Kubernetes_Helper import *
from KubeResources import *
from GeneticSched import *


## letss start with the tasks cpus's as the state
## selection will be basd on

class CloudEnv(gym.Env):
    def __init__(self, steps):
        """
        Action space : discrete : Genetic, Kube default scheduler
        Observation space / same state space : we can maybe start with the nb of tasks and their cpu usage and the
        available nodes and maybeee later we can alter the nodes resources

        """
        super(CloudEnv, self).__init__()
        self.nodes = nodes_available()
        self.VMSnumber = len(self.nodes)
        self.steps = steps
        self.currentsteps = 0
        self.lastmetrics = None

    def step(self, action):
        """
        for each step run one scheduling algo and wait a bit for results and get them and delete pods and restart them
        maybe each time we re-run we run random number of replicas set so that we can vary and change the
        agent's experience
        :param action:
        :return:
        """
        self.currentsteps = self.currentsteps + 1
        if action == 0:
            algo = 'genetic'
        elif action == 1:
            algo = 'defalu'
        reconfigure(algo)
        time.sleep(40)
        if algo == 'genetic':
            schedule()
        ## get mesurmùents  stock them inside the reaply memory ( in the training loop )
        state = get_state()
        reward = self.reward()
        done = self.termination()
        return action, state, reward, done

    def reset(self):
        """
        MAYBE WE DO NOT NEED THIIS
        reset the tasks, Deleting all the envi, looking again for availble nodes,
        :return:
        """
        ## reseting tasks with random CPU between the values and the scheduler name as waiting
        pass

    def termination(self):
        """
        check maybe the number of steps of our agent if we attented that time step we stop
        :return:
        """
        done = False
        if self.steps == self.currentsteps:
            done = True

        return done

    def reward(self):
        """
        what is our reward function.. this a prob for now
        maybe try one time get the actual mesruements of that cpu of the node
        and on the next
        LATTEEEEER check the condiciton of nodes if one pod got effectied he gets --
        :return:
        """
        if self.currentsteps == 0:  # cant compare til we have two time steps
            reward = 1
            self.lastmetrics = [metric()]
        else:
            imbalence_deg, exec_time = metric()
            if imbalence_deg < self.lastmetrics[0]:
                if exec_time < self.lastmetrics[1]:
                    reward = 5
                else:
                    reward = 3
            else:
                if exec_time < self.lastmetrics[1]:
                    reward = 3
                else:
                    reward = -1
            self.lastmetrics = metric()
        return reward


# def metrics(cpu, mem):
#     ## compute the avg cpu util to calculte the avg cpu util
#     ## no neeed to compute the avg, it's always done
#     for i in zip:
#         pass
#     avg = 0