#from Agent import *
from envi import CloudEnv
from maintest import DQNAgent
from utils.KubeResources import *
import sys
import torch
sys.path.insert(0, './PPO/train_PPO.py')
from PPO.train_PPO import *

env = CloudEnv()

algos = {0: 'genetic', 1: 'scheduler-round-robin'}
state_size = 2
action_size = len(algos)

#agent = DQNAgent(state_size, action_size)
#agent.load("models/agent-dqn.h5")
#model.load_state_dict(torch.load("PPO/models/PPO_discrete_CloudEnv.pth"))
#model.eval()
agentres, defaultres = [], []

ppo = PPO(state_size, action_size, parameters['lr'], parameters['betas'], parameters['gamma']
          , parameters['K_epochs'], parameters['eps_clip'], ckpt=parameters['ckpt_folder'])
for i in range(5):
    print('Starting the first iteration test')
    state = env.reset(True)
    print(state)
    action = agent.act(state)
    _, metrics = env.step(action)
    print(f'Agent took {algos[action]} in state {state} gave exec time {metrics[0]} and imbal deg {metrics[1]}')
    agentres.append(metrics)

    state = env.reset(False)
    reconfigure('default-scheduler')
    metrics = resources()
    print(f'Default scheduler in state {state} gave exec time {metrics[0]} and imbal def {metrics[1]} ')
    defaultres.append(metrics)

print('agent')
print(agentres)
print('default')
print(defaultres)
