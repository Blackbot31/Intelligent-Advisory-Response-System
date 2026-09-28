"""
Two learning variants of the Coordination and Control Engine, sharing the
identical network architecture used in the paper (subsystems/cce.py):
    Linear(10,128) - ReLU - Linear(128,128) - ReLU - Linear(128,4)

Route A - CorrectedDQN:
    A genuine Deep Q-Network. The ORIGINAL training in
    training/historical_data.py only ever stored the correct action with a
    positive reward and never sampled the alternatives, so the value function
    had no way to learn that other actions are worse (every Q-value drifted
    toward ~1.0 and argmax became arbitrary -> chance accuracy).
    This version fixes the experience collection: each scenario is a one-step
    episode, actions are chosen epsilon-greedily so ALL actions are eventually
    experienced, and the contrastive reward (+1 correct, -1 incorrect) lets
    Q(s, best) rise and Q(s, wrong) fall. A target network is used for the
    bootstrap term, as is standard for DQN.

Route B - SupervisedCCE:
    Treats the labelled (state -> best_action) data as what it actually is --
    a classification problem -- and trains the same network with cross-entropy.

Both expose .fit(X, y) and .predict(X); CorrectedDQN also records a learning
curve (per-episode moving accuracy) for plotting.
"""
import numpy as np
import torch
import torch.nn as nn


def _make_net(state_size=10, action_size=4):
    return nn.Sequential(
        nn.Linear(state_size, 128), nn.ReLU(),
        nn.Linear(128, 128), nn.ReLU(),
        nn.Linear(128, action_size),
    )


def set_seed(seed):
    import random
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


# ---------------------------------------------------------------------------
# Route B: supervised classifier
# ---------------------------------------------------------------------------
class SupervisedCCE:
    def __init__(self, state_size=10, action_size=4, lr=0.01, epochs=300, seed=0):
        set_seed(seed)
        self.net = _make_net(state_size, action_size)
        self.opt = torch.optim.Adam(self.net.parameters(), lr=lr)
        self.lossf = nn.CrossEntropyLoss()
        self.epochs = epochs
        self.loss_curve = []

    def fit(self, X, y):
        Xt = torch.tensor(X, dtype=torch.float32)
        yt = torch.tensor(y, dtype=torch.long)
        self.net.train()
        for _ in range(self.epochs):
            self.opt.zero_grad()
            out = self.net(Xt)
            loss = self.lossf(out, yt)
            loss.backward()
            self.opt.step()
            self.loss_curve.append(float(loss.item()))
        return self

    def predict(self, X):
        self.net.eval()
        with torch.no_grad():
            out = self.net(torch.tensor(X, dtype=torch.float32))
        return out.argmax(1).numpy().astype(np.int64)

    def predict_proba(self, X):
        self.net.eval()
        with torch.no_grad():
            out = self.net(torch.tensor(X, dtype=torch.float32))
            return torch.softmax(out, dim=1).numpy()


# ---------------------------------------------------------------------------
# Route A: corrected genuine DQN
# ---------------------------------------------------------------------------
class CorrectedDQN:
    def __init__(self, state_size=10, action_size=4, lr=0.001, gamma=0.95,
                 epsilon=1.0, epsilon_min=0.01, epsilon_decay=0.995,
                 episodes=1500, batch_size=32, target_sync=25, seed=0):
        set_seed(seed)
        self.action_size = action_size
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.episodes = episodes
        self.batch_size = batch_size
        self.target_sync = target_sync
        self.net = _make_net(state_size, action_size)
        self.target = _make_net(state_size, action_size)
        self.target.load_state_dict(self.net.state_dict())
        self.opt = torch.optim.Adam(self.net.parameters(), lr=lr)
        self.lossf = nn.MSELoss()
        from collections import deque
        self.memory = deque(maxlen=2000)
        self.learning_curve = []   # (episode, moving_accuracy)

    def _reward(self, action, best_action):
        return 1.0 if action == best_action else -1.0

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return np.random.randint(self.action_size)
        with torch.no_grad():
            q = self.net(torch.tensor(state, dtype=torch.float32).unsqueeze(0))
        return int(q.argmax().item())

    def _replay(self):
        if len(self.memory) < self.batch_size:
            return
        import random
        batch = random.sample(self.memory, self.batch_size)
        s = torch.tensor(np.array([b[0] for b in batch]), dtype=torch.float32)
        a = torch.tensor([b[1] for b in batch], dtype=torch.long)
        r = torch.tensor([b[2] for b in batch], dtype=torch.float32)
        # one-step contextual episodes: done=True, so no bootstrap term needed,
        # but we keep the target network for faithfulness to the DQN formulation.
        q = self.net(s)
        q_a = q.gather(1, a.unsqueeze(1)).squeeze(1)
        target = r  # done=True for every scenario
        loss = self.lossf(q_a, target)
        self.opt.zero_grad()
        loss.backward()
        self.opt.step()

    def fit(self, X, y):
        n = len(X)
        recent = []
        for ep in range(self.episodes):
            i = np.random.randint(n)
            state, best = X[i], int(y[i])
            action = self.act(state)
            reward = self._reward(action, best)
            self.memory.append((state, action, reward, state, True))
            self._replay()
            if self.epsilon > self.epsilon_min:
                self.epsilon *= self.epsilon_decay
            if ep % self.target_sync == 0:
                self.target.load_state_dict(self.net.state_dict())
            # track greedy accuracy on a rolling basis every 50 episodes
            if ep % 50 == 0:
                acc = float(np.mean(self.predict(X) == y))
                self.learning_curve.append((ep, acc))
        return self

    def predict(self, X):
        with torch.no_grad():
            q = self.net(torch.tensor(np.array(X), dtype=torch.float32))
        return q.argmax(1).numpy().astype(np.int64)

    def confidence(self, X):
        """Proper confidence: softmax over Q-values of the chosen action.
        Replaces the cosmetic (1 - epsilon) used in the original code."""
        with torch.no_grad():
            q = self.net(torch.tensor(np.array(X), dtype=torch.float32))
            p = torch.softmax(q, dim=1).numpy()
        return p.max(1)
