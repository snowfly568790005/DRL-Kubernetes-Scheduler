from os.path import exists
from torch.utils.tensorboard import SummaryWriter
import pandas as pd
import sys

sys.path.insert(0, './PPO')
from PPO.PPO import *
from PPO.PPO_Params import *


def trainPPO(env):
    writer = SummaryWriter()
    state_size = 2
    action_size = len(env.actions)
    tb = False

    ckpt = parameters['ckpt_folder'] + '/PPO_discrete_CloudEnv' + '.pth'

    memory = Memory()

    ppo = PPO(state_size, action_size, parameters['lr'], parameters['betas'], parameters['gamma']
              , parameters['K_epochs'], parameters['eps_clip'], ckpt=ckpt)

    running_reward, avg_length, time_step = 0, 0, 0

    # training loop
    scores = []
    for i_episode in range(1, parameters['max_episodes'] + 1):
        state = env.reset(True)
        action_list = []
        for steps in range(parameters['max_timesteps']):
            state = env.reset(False)
            time_step += 1

            action = ppo.select_action(state, memory)
            action_list.append(env.actions[action])

            _, next_state, immediate_reward, done = env.step(action)

            memory.rewards.append(immediate_reward)
            memory.is_terminals.append(done)

            data = {
                'action': env.actions[action],
                'reward': immediate_reward,
                'state': state,
                'done': done
            }
            df = pd.DataFrame([data])
            if exists('PPO/results.csv'):
                df.to_csv('PPO/results.csv', mode='a', index=False, header=False)
            else:
                df.to_csv('PPO/results.csv', encoding='utf-8', index=False)

            if time_step % parameters['update_timesteps'] == 0:
                ppo.update(memory)
            memory.clear_memory()
            time_step = 0
            print(f'step {steps} is done, state {state} with reward {immediate_reward}')
            running_reward += immediate_reward
            if done:
                break
        avg_length += steps
        scores.append(running_reward)

        print(f'{i_episode} is done, state {state} with series of actions {action_list} and final score {scores[-1]} ')

        if i_episode % parameters['save_interval'] == 0:
            torch.save(ppo.policy.state_dict(),  'PPO/models/PPO_discrete_CloudEnv.pth')
            print('Save a checkpoint!')

        if tb:
            writer.add_scalar('scalar/reward', running_reward, i_episode)
            writer.add_scalar('scalar/length', avg_length, i_episode)

            running_reward, avg_length = 0, 0
    return scores
