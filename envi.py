import time
from os.path import exists
import gym
from utils.KubeResources import *
from algos.GeneticSched import *


class CloudEnv:
    def __init__(self):
        """
        Action space : discrete : Genetic, Kube default scheduler
        Observation space / same state space : we can maybe start with the nb of tasks and their cpu usage and the
        available nodes and maybe later we can alter the nodes resources

        """
        super(CloudEnv, self).__init__()
        self.episode_steps = 0
        self.last_metrics = None
        self.same_results = 0
        self.better_rest = False
        self.actions = {0: 'genetic', 1: 'scheduler-round-robin'}

    def step_test(self, action):
        """
        for each step run one scheduling algo and wait a bit for results and get them and delete pods and restart them
        maybe each time we re-run we run random number of replicas set so that we can vary and change the
        agent's experience
        :param action:
        :return:

        FOR TESTIING
        """
        reconfigure(self.actions[action])
        time.sleep(5)
        if self.actions[action] == 'genetic':
            schedule()
        time.sleep(5)
        metrics = resources()
        return metrics  # for testing

    def step(self, action, kubernetes_metrics):
        """
        for each step run one scheduling algo and wait a bit for results and get them and delete pods and restart them
        maybe each time we re-run we run random number of replicas set so that we can vary and change the
        agent's experience
        :param kubernetes_metrics:
        :param action:
        :return:
        """
        reconfigure(self.actions[action])
        time.sleep(5)
        if self.actions[action] == 'genetic':
            schedule()
        time.sleep(5)
        metrics = resources()  # [1] for training and without for testing
        reward = self.reward(metrics, kubernetes_metrics)
        done = self.termination()
        next_state = get_nextstate()
        self.episode_steps = self.episode_steps + 1
        #return metrics  # for testing
        return action, next_state, reward, done  # for training

    def reset(self, new_epi):
        if new_epi:
            self.last_metrics = None
            self.episode_steps = 0
            self.better_rest = False
        state = reset(new_epi)
        return state

    def termination(self):
        """
        check maybe the number of steps of our agent if we attended that time step we stop
        :return:
        """
        if self.better_rest:
            return True
        return False

    def reward(self, metrics, kubernetes_metrics):
        """
        what is our reward function. this a prob for now
        maybe try one time get the actual measurements of that cpu of the node
        and on the next
        Later check the condition of nodes if one pod got effected h
        :return:
        """
        if metrics <= kubernetes_metrics:
            reward = 3
            self.better_rest = True
        else:
            reward = -1
        return reward
