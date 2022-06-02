import torch

from Agent import *
from envi import *

## epiode is not the number of steps withing an agent
##

## get all states,
env = CloudEnv()
_ = env.reset()
algos = {0: 'genetic', 1: 'default-scheduler', 2: 'round-robin'}
print(get_tasks())
state_size = len(get_tasks())
action_size = len(algos)
print('state size', state_size)
print('action_size', action_size)
agent = Agent(state_size, action_size, 10)



def dqn(n_eps=1000, eps_start=0.1, eps_end=0.01, eps_decay=0.995):
    scores = []
    eps = eps_start
    for i in range(1, n_eps + 1):
        state = env.reset()  ## this is where we are going to reset the env with new tasks and random cpu in range
        print(f'done resetting for {i} th time')
        action = agent.act(state, eps)
        print(f'agent gave action {algos[action]} and action is {action}')
        ## matp this to the dict
        _, next_state, reward, done = env.step(action)
        print(f'got {reward}')
        agent.step(state, action, reward, next_state, done)
        scores.append(reward)
        eps = max(eps_end, eps_decay * eps)
        print(f'{i} th step is done')
        print('////////////////////////////////////////')
    ## we save the model here
    torch.save(agent.qnetwork_local.state_dict(), 'checkpt_Gen_Default.pth')
    return scores

scores = dqn()
print(scores)

fig = plt.figure()
ax = fig.add_subplot(111)
plt.plot(np.arange(len(scores)-1), scores[1::]) # ignore the first score
plt.ylabel('Score')
plt.xlabel('Episode #')
plt.show()