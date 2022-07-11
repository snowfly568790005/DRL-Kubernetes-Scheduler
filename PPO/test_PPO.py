from os.path import exists
import pandas as pd
import sys

import PPO
from PPO_Params import parameters
from envi import *
import torch


def testPPO(env):
    state_size = 2
    action_size = len(env.actions)
    tb = False

    ckpt = "models/PPO_discrete_CloudEnv.pth"

    memory = PPO.Memory()

    ppo = PPO.PPO(state_size, action_size, parameters['lr'], parameters['betas'], parameters['gamma']
              , parameters['K_epochs'], parameters['eps_clip'])
    ppo.policy.load_state_dict(torch.load("models/PPO_discrete_CloudEnv.pth"))

    for i_episode in range(5):
        ppo.policy.eval()
        state = env.reset(True)
        print('//////////////////////////')
        print(f'Starting {i_episode} iteration with state {state}')

        action = ppo.select_action(state, memory)

        execution_time, imbal_deg = env.step(action)

        data = {
            'agent': 'PPO_Agent',
            'action': env.actions[action],
            'state': state,
            'execution_time': execution_time,
            'imbal_deg': imbal_deg
        }
        df = pd.DataFrame([data])
        if exists('tests.csv'):
            df.to_csv('tests.csv', mode='a', index=False, header=False)
        else:
            df.to_csv('tests.csv', encoding='utf-8', index=False)

        print(f'PPO Agent gave {env.actions[action]}')
        print('Starting default')
        state = env.reset(False)
        reconfigure('default-scheduler')
        execution_time, imbal_deg = resources()
        data = {
            'agent': 'default-scheduler',
            'action': -1,
            'state': state,
            'execution_time': execution_time,
            'imbal_deg': imbal_deg
        }
        df = pd.DataFrame([data])
        df.to_csv('tests.csv', mode='a', index=False, header=False)


env = CloudEnv()
testPPO(env)
