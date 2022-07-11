from Agent import *
from envi import *

import sys
sys.path.insert(0, './PPO/train_PPO.py')
from PPO.train_PPO import trainPPO

env = CloudEnv()
#
# agent.qnetwork_local.load_state_dict(torch.load('checkpt_gen_rr2_26.pth'))
#
#
# def dqn(n_eps=74, steps=10, eps_start=0.4, eps_end=0.01, eps_decay=0.995):
#     scores = []
#     eps = eps_start
#     for i in range(1, n_eps + 1):
#         state = env.reset(True)
#         score = 0
#         for step in range(steps):
#             env.reset(False)
#             action = agent.act(state, eps)
#             _, next_state, reward, done = env.step(action)
#             agent.step(state, action, reward, next_state, done)
#             data = {
#                 'action': action,
#                 'reward': reward,
#                 'state': state,
#                 'done': done
#             }
#             df = pd.DataFrame([data])
#             if exists('data/results.csv'):
#                 df.to_csv('data/results.csv', mode='a', index=False, header=False)
#             else:
#                 df.to_csv('data/results.csv', encoding='utf-8', index=False)
#             score = score + reward
#             if done:
#                 break
#             print(
#                 f'{i} th step is done with state {state} and next state {next_state} and total reward {score} with '
#                 f'action {algos[action]}  with done {done} in {step} steps')
#             print('////////////////////////////////////////')
#         eps = max(eps_end, eps_decay * eps)
#         scores.append(score)
#         name = f'checkpt_gen_rr2_{i}.pth'
#         torch.save(agent.qnetwork_local.state_dict(), name)
#         if os.path.exists(f'checkpt_gen_rr2_{i - 1}.pth'):
#             os.remove(f'checkpt_gen_rr2_{i - 1}.pth')
#     return scores


scores = trainPPO(env)
print(scores)

fig = plt.figure()
ax = fig.add_subplot(111)
plt.plot(np.arange(len(scores) - 1), scores[1::])  # ignore the first score
plt.ylabel('Score')
plt.xlabel('Episode #')
plt.show()
