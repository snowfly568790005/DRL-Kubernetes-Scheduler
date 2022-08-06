import random
import numpy as np
from collections import deque
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam
from envi import *
import matplotlib.pyplot as plt

EPISODES = 500


class DQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95  # discount rate
        self.epsilon = 1.0  # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.model = self._build_model()

    def _build_model(self):
        # Neural Net for Deep-Q learning Model
        model = Sequential()
        model.add(Dense(24, input_dim=self.state_size, activation='relu'))
        model.add(Dense(24, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse',
                      optimizer=Adam(learning_rate=self.learning_rate))
        # ADD VERBOZE =0
        return model

    def memorize(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        act_values = self.model.predict(state)
        return np.argmax(act_values[0])  # returns action

    def replay(self, batch_size):
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target = (reward + self.gamma *
                          np.amax(self.model.predict(next_state)[0]))
            target_f = self.model.predict(state)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def load(self, name):
        self.model.load_weights(name)

    def save(self, name):
        self.model.save_weights(name)


def train():
    env = CloudEnv()
    state = env.reset(False)
    algos = {0: 'genetic', 1: 'scheduler-round-robin'}
    state_size = 2
    action_size = len(algos)
    agent = DQNAgent(state_size, action_size)
    agent.load("newagent-dqn.h5")
    done = False
    batch_size = 10
    scores = []
    for e in range(EPISODES):
        state = env.reset(True)
        state = np.reshape(state, [1, state_size])
        print(f'Starting episode {e} with state {state}')
        score = 0
        reconfigure('default-scheduler')
        metrics = resources()
        for time in range(10):
            env.reset(False)
            action = agent.act(state)
            _, next_state, reward, done = env.step(action, metrics)
            next_state = np.reshape(next_state, [1, state_size])
            agent.memorize(state, action, reward, next_state, done)
            score = score + reward
            data = {
                'action': env.actions[action],
                'reward': reward,
                'state': state,
                'done': done
            }
            df = pd.DataFrame([data])
            if exists('results.csv'):
                df.to_csv('results.csv', mode='a', index=False, header=False)
            else:
                df.to_csv('results.csv', encoding='utf-8', index=False)
            if done:
                print(f'episode {e} done after {time} timesteps')
                break
            if len(agent.memory) > batch_size:
                agent.replay(batch_size)
        scores.append(score)
        if e % 2 == 0:
            agent.save("newtrainagent-dqn.h5")
    return scores


if __name__ == "__main__":
    scores = train()
    print(scores)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.plot(np.arange(len(scores) - 1), scores[1::])  # ignore the first score
    plt.ylabel('Score')
    plt.xlabel('Episode #')
    plt.show()
