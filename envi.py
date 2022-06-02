import gym
from Kubernetes_Helper import *
from KubeResources import *
from GeneticSched import *


## letss start with the tasks cpus's as the state
## selection will be basd on

class CloudEnv(gym.Env):
    def __init__(self):
        """
        Action space : discrete : Genetic, Kube default scheduler
        Observation space / same state space : we can maybe start with the nb of tasks and their cpu usage and the
        available nodes and maybeee later we can alter the nodes resources

        """
        super(CloudEnv, self).__init__()
        # self.nodes = nodes_available()
        self.currentsteps = 0
        self.lastmetrics = None
        self.algos = {0: 'genetic', 1: 'default-scheduler'}

    def getmetrics(self):
        if self.currentsteps == 0:
            return None
        else:
            return metric()

    def step(self, action):
        """
        for each step run one scheduling algo and wait a bit for results and get them and delete pods and restart them
        maybe each time we re-run we run random number of replicas set so that we can vary and change the
        agent's experience
        :param action:
        :return:
        """
        reconfigure(self.algos[action])
        time.sleep(40)
        if self.algos[action] == 'genetic':
            schedule()
        next_state, metrics = resources()
        reward = self.reward(metrics)
        done = self.termination()
        self.currentsteps = self.currentsteps + 1
        return action, next_state, reward, done

    def reset(self):
        """
        MAYBE WE DO NOT NEED THIIS
        reset the tasks, Deleting all the envi, looking again for availble nodes,
        :return:
        """
        ## reseting tasks with random CPU between the values and the scheduler name as waiting
        return reset()

    def termination(self):
        """
        check maybe the number of steps of our agent if we attented that time step we stop
        :return:
        """
        ## we change this to kube checks if all tasks are done in case of evicted tasks
        return True

    def reward(self,metrics):
        """
        what is our reward function.. this a prob for now
        maybe try one time get the actual mesruements of that cpu of the node
        and on the next
        LATTEEEEER check the condiciton of nodes if one pod got effectied he gets --
        :return:
        """
        if self.currentsteps == 0:  # cant compare til we have two time steps
            reward = 1
            self.lastmetrics = metrics
        else:
            print('self.lastmetrics[0]', self.lastmetrics[0])
            print('self.lastmetrics[1]', self.lastmetrics[1])
            exec_time, imbalence_deg = metrics[0], metrics[1]
            if imbalence_deg < self.lastmetrics[1]:
                if exec_time < self.lastmetrics[0]:
                    reward = 5
                else:
                    reward = 3
            else:
                if exec_time < self.lastmetrics[0]:
                    reward = 3
                else:
                    reward = -1
            self.lastmetrics = metrics
        return reward
