import collections
import time
import numpy as np

import gym
from Kubernetes_Helper import *
from KubeResources import *


## letss start with the tasks cpus's as the state
## selection will be basd on

class CloudEnv(gym.Env):
    def __init__(self, steps):
        """
        Action space : discrite : Genetic, Kube default scheuduler
        Observation space / same state space : we can maybz start with the nb of tasks and their cpu usage and the
        availabe nodes and maybeee later we can alter the nodes resources

        """
        super(CloudEnv, self).__init__()
        self.nodes = nodes_available()
        self.VMSnumber = len(self.nodes)
        self.tasks = tasks()
        self.steps = steps
        self.currentsteps = 0

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
        ## this is when I reconfigure the pods to change their scduler name
        reconfigure(algo)
        ## if genetic is the algo we call the genetic funtion
        ## we do not need to this for the others for now
        time.sleep(10)  ## modify later
        ## get mesurmùents  stock them inside the reaply memory ( in the training loop )
        # pass thiss to the reward

        cpunode, memnode, exec_tuime = resources()
        state = {'cpu': cpunode, 'memory': memnode}
        ## call memory replay and annd tihds
        reward = self.reward()
        done = self.termination()
        return action, state, reward, done

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
        if self.currentsteps == 0:
            reward = 1
        else:
            cpunode, memnode, exec_tuime = resources()
            ### compare metrics
        return reward


class ReplayMemory:
    def __init__(self, capacity):
        self.memory = collections.deque(maxlen=capacity)

    def __len__(self):
        return len(self.memory)

    def append(self, experience):
        self.memory.append(experience)

    def tocsv(self):
        pass

    def sample(self, batch_size):
        indices = np.random.choice(len(self.memory), batch_size,
                                   replace=False)
        states, actions, rewards, dones, next_states = zip([self.memory[idx] for idx in indices])

        ## will see with the return, depends on our state
        return np.array(states), np.array(actions), np.array(rewards, dtype=np.float32), \
               np.array(dones, dtype=np.uint8), np.array(next_states)
