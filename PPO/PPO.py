import torch
import torch.nn as nn
from torch.distributions import Categorical

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


class Memory:  # collected from old policy
    def __init__(self):
        self.states = []
        self.actions = []
        self.rewards = []
        self.is_terminals = []
        self.logprobs = []

    def clear_memory(self):
        del self.states[:]
        del self.actions[:]
        del self.rewards[:]
        del self.is_terminals[:]
        del self.logprobs[:]


class ActorCritic(nn.Module):
    def __init__(self, state_dim, action_dim):
        super(ActorCritic, self).__init__()

        self.actor = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.Tanh(),
            nn.Linear(64, 32),
            nn.Tanh(),
            nn.Linear(32, action_dim),
            nn.Softmax(dim=-1)  # For discrete actions, we use softmax policy
        )

        self.critic = nn.Sequential(
            nn.Linear(state_dim, 64),
            nn.Tanh(),
            nn.Linear(64, 32),
            nn.Tanh(),
            nn.Linear(32, 1)
        )

    def act(self, state, memory):  # state (1,8)
        action_probs = self.actor(state)  # (1,4)
        dist = Categorical(
            action_probs)  # distribution func: sample an action (return the corresponding index) according to the probs
        action = dist.sample()
        action_logprob = dist.log_prob(action)  # (1,)

        memory.states.append(state)
        memory.actions.append(action)
        memory.logprobs.append(action_logprob)
        # print(action_probs.size(), action_logprob.size(), action.size())
        return action.item()  # convert to scalar

    def evaluate(self, state, action):  # state (2000, 8); action (2000, 4)
        state_value = self.critic(state)  # (2000, 1)

        # to calculate action score(logprobs) and distribution entropy
        action_probs = self.actor(state)  # (2000,4)
        dist = Categorical(action_probs)
        action_logprobs = dist.log_prob(action)  # (2000, 1)
        dist_entropy = dist.entropy()

        return action_logprobs, torch.squeeze(state_value),


class PPO:
    def __init__(self, state_dim, action_dim, lr, betas, gamma, K_epochs, eps_clip, restore=False, ckpt=None):
        self.lr = lr
        self.betas = betas
        self.gamma = gamma
        self.eps_clip = eps_clip
        self.K_epochs = K_epochs

        # current policy
        self.policy = ActorCritic(state_dim, action_dim).to(device)
        #if restore:
        #    pretained_model = torch.load(ckpt, map_location=lambda storage, loc: storage)
        #    self.policy.load_state_dict(pretained_model)
        self.optimizer = torch.optim.Adam(self.policy.parameters(), lr=lr, betas=betas)

        # old policy: initialize old policy with current policy's parameter
        self.old_policy = ActorCritic(state_dim, action_dim).to(device)
        self.old_policy.load_state_dict(self.policy.state_dict())

        self.MSE_loss = nn.MSELoss()  # to calculate critic loss

    def select_action(self, state, memory):
        state = torch.FloatTensor(state.reshape(1, -1)).to(device)  # flatten the state
        return self.old_policy.act(state, memory)

    def update(self, memory):
        # Monte Carlo estimation of rewards
        rewards = []
        discounted_reward = 0
        for reward, is_terminal in zip(reversed(memory.rewards), reversed(memory.is_terminals)):
            if is_terminal:
                discounted_reward = 0
            discounted_reward = reward + self.gamma * discounted_reward
            rewards.insert(0, discounted_reward)

        # Normalize rewards
        rewards = torch.tensor(rewards).to(device)
        rewards = (rewards - rewards.mean()) / (rewards.std() + 1e-5)

        # convert list to tensor
        old_states = torch.squeeze(torch.stack(memory.states).to(device)).detach()
        old_actions = torch.squeeze(torch.stack(memory.actions).to(device)).detach()
        old_logprobs = torch.squeeze(torch.stack(memory.logprobs)).to(device).detach()

        # Train policy for K epochs: sampling and updating
        for _ in range(self.K_epochs):
            # Evaluate old actions and values using current policy
            logprobs, state_values, dist_entropy = self.policy.evaluate(old_states, old_actions)

            # Importance ratio: p/q
            ratios = torch.exp(logprobs - old_logprobs.detach())

            # Advantages
            advantages = rewards - state_values.detach()  # old states' rewards - old states' value( evaluated by current policy)

            # Actor loss using Surrogate loss
            surr1 = ratios * advantages
            surr2 = torch.clamp(ratios, 1 - self.eps_clip, 1 + self.eps_clip) * advantages
            actor_loss = - torch.min(surr1, surr2)

            # Critic loss: critic loss - entropy
            critic_loss = 0.5 * self.MSE_loss(rewards, state_values) - 0.01 * dist_entropy

            # Total loss
            loss = actor_loss + critic_loss

            # Backward gradients
            self.optimizer.zero_grad()
            loss.mean().backward()
            self.optimizer.step()

        # Copy new weights to old_policy
        self.old_policy.load_state_dict(self.policy.state_dict())