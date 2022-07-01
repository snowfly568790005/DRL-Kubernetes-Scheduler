from Agent import *
from envi import *
from maintest import *

env = CloudEnv()

algos = {0: 'genetic', 1: 'scheduler-round-robin'}
state_size = 2
action_size = len(algos)

agent = DQNAgent(state_size, action_size)
agent.load("agent-dqn.h5")
agentres, defaultres = [], []
for i in range(5):
    print('Starting the first iteration test')
    state = env.reset(True)
    print(state)
    action = agent.act(state)
    _, metrics = env.step(action)
    print(f'Agent took {algos[action]} in state {state} gave exec time {metrics[0]} and imbal deg {metrics[1]}')
    agentres.append(metrics)

    reconfigure('kube-scheduler')
    metrics = resources()
    print(f'Default scheduler in state {state} gave exec time {metrics[0]} and imbal def {metrics[1]} ')
    defaultres.append(metrics)

print('agent')
print(agentres)
print('default')
print(defaultres)
