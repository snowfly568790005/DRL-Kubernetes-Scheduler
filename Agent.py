from model import *
from ReplayMemory import *
import torch
import torch.optim as optim

BUFFER_SIZE = int(1e5)  # replay buffer size
BATCH_SIZE = 2  # minibatch size
GAMMA = 0.90  # discount factor
TAU = 1e-3  # for soft update of target parameters
LR = 0.01  # learning rate
UPDATE_EVERY = 4  # how often to update the network

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


## next states is the resulat of that specfuc actuon

class Agent:
    def __init__(self, state_size, action_size, seed):
        self.state_size = state_size
        self.action_size = action_size
        random.seed(seed)

        self.qnetwork_local = QNetwork(state_size, action_size, seed).to(device)
        self.qnetwork_target = QNetwork(state_size, action_size, seed).to(device)
        self.optimizer = optim.Adam(self.qnetwork_local.parameters(), lr=LR)

        self.memory = ReplayBuffer(action_size, BUFFER_SIZE, BATCH_SIZE, seed)

    def step(self, state, action, reward, next_state, done):
        self.memory.add(state, action, reward, next_state, done)
        if len(self.memory) > BATCH_SIZE:
                experience = self.memory.sample()
                self.learn(experience)

    def learn(self, experience):
        """
         update network based of experience sample
         :param experience:
         :return:
         """
        states, actions, rewards, next_states, dones = experience
        oldval = self.qnetwork_local(states).gather(-1, actions)
        with torch.no_grad():
            next_action = self.qnetwork_local(next_states).argmax(-1, keepdims=True)
            maxQ = self.qnetwork_target(next_states).gather(-1, next_action)
            target = rewards + GAMMA * maxQ * (1 - dones)
        loss = F.mse_loss(oldval, target)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        self.updateparam(self.qnetwork_local, self.qnetwork_target, TAU)

    def updateparam(self, local_model, target_model, tau):
        for target_param, local_param in zip(target_model.parameters(), local_model.parameters()):
            target_param.data.copy_(tau * local_param.data + (1.0 - tau) * target_param.data)

    def act(self, state, eps=0.):
        """
        greedy policy

        :param state:
        :param eps:
        :return:
        """
        state = torch.unsqueeze(torch.FloatTensor(state), 0)  # get a 1D array
        if np.random.randn() <= eps:  # greedy policy
            action_value = self.qnetwork_local.forward(state)
            return np.argmax(action_value.cpu().data.numpy())
        else:  # random policy
            return random.choice(np.arange(self.action_size))

        # state = torch.from_numpy(state).float().unsqueeze(0).to(device)
        # self.qnetwork_local.eval()
        # with torch.no_grad():
        #     actions = self.qnetwork_local(state)
        # self.qnetwork_local.train()
        # print(actions)
        # if random.random() < eps:
        #     print(random.choice(np.arange(self.action_size)), 'random')
        #     return random.choice(np.arange(self.action_size))
        # else:
        #     print(np.argmax(actions.cpu().data.numpy()))
        #     return np.argmax(actions.cpu().data.numpy())

