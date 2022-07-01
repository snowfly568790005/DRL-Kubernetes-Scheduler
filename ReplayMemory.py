from collections import namedtuple, deque
import random
import numpy as np
import pandas as pd
import torch

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


class ReplayBuffer:
    """Fixed-size buffer to store experience tuples."""

    def __init__(self, action_size, buffer_size, batch_size, seed):
        """Initialize a ReplayBuffer object.
        Params
        ======
            action_size (int): dimension of each action
            buffer_size (int): maximum size of buffer
            batch_size (int): size of each training batch
            seed (int): random seed
        """
        self.action_size = action_size
        self.memory = deque(maxlen=buffer_size)
        self.batch_size = batch_size
        self.experience = namedtuple("Experience", field_names=["states", "actions", "rewards", "next_states", "dones"])
        random.seed(seed)

    def add(self, state, action, reward, next_states, done):
        """Add a new experience to memory."""
        e = self.experience(state, action, reward, next_states, done)
        self.memory.append(e)
        self.add_txt(state, action, reward, next_states, done)

    def sample(self):
        """Randomly sample a batch of experiences from memory."""
        experiences = random.sample(self.memory, k=self.batch_size)

        states = torch.from_numpy(np.vstack([e.states for e in experiences if e is not None])).float().to(device)
        actions = torch.from_numpy(np.vstack([e.actions for e in experiences if e is not None])).long().to(device)
        next_states = torch.from_numpy(np.vstack([e.next_states for e in experiences if e is not None])).float().to(
            device)
        rewards = torch.from_numpy(np.vstack([e.rewards for e in experiences if e is not None])).float().to(device)
        dones = torch.from_numpy(
            np.vstack([e.dones for e in experiences if e is not None]).astype(np.uint8)).float().to(
            device)

        return (states, actions, rewards, next_states, dones)

    def __len__(self):
        """Return the current size of internal memory."""
        return len(self.memory)

    def add_txt(self, state, action, reward, next_states, done):
        with open("data/results", 'a') as file:
            text = f"{state} {action} {reward} {next_states[0]} {next_states[1]} {done} \n"
            file.write(text)
            file.close()
