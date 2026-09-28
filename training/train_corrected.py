"""
Corrected training for the Coordination and Control Engine.

Background
----------
The original training loop (training/historical_data.py) stored ONLY the
expert 'best_action' for each scenario, always with a positive reward, and
never sampled the alternative actions. A Q-learning update can only learn to
*prefer* one action over another if it also sees the others carry lower value;
because the wrong actions were never experienced, every Q-value drifted toward
~1.0 and the greedy policy became arbitrary (chance-level accuracy).

Fix
---
This script keeps the identical network (subsystems/cce.py) and its save format,
but corrects the experience collection:
  * each scenario is treated as a one-step episode,
  * actions are chosen epsilon-greedily so ALL four actions are eventually tried,
  * a contrastive reward (+1 for the expert action, -1 otherwise) gives the
    value function the signal it needs to discriminate,
  * training runs for enough episodes for epsilon to decay toward its floor.

The resulting model is saved to models/cce_model.pt in the same format the live
system loads, so the deployed CCE uses a policy that has genuinely learned.
"""
import sys
import os
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from subsystems.cce import CoordinationControlEngine
from training.historical_data import HISTORICAL_SCENARIOS


def train_corrected(episodes=4000, seed=0, verbose=True):
    import random
    random.seed(seed)
    np.random.seed(seed)
    import torch
    torch.manual_seed(seed)

    cce = CoordinationControlEngine(state_size=10, action_size=4)
    X = [s["state"] for s in HISTORICAL_SCENARIOS]
    y = [s["best_action"] for s in HISTORICAL_SCENARIOS]
    n = len(X)

    for ep in range(episodes):
        i = np.random.randint(n)
        state, best = X[i], y[i]
        action = cce.act(state)                      # epsilon-greedy
        reward = 1.0 if action == best else -1.0     # contrastive reward
        next_state = [max(0, s * 0.95) for s in state]
        cce.remember(state, action, reward, next_state, True)
        cce.replay(batch_size=min(32, len(cce.memory)))

    # greedy accuracy on the expert scenarios
    cce.epsilon = 0.0
    import torch
    correct = 0
    for s in HISTORICAL_SCENARIOS:
        with torch.no_grad():
            q = cce.model(torch.FloatTensor(s["state"]).unsqueeze(0)).numpy()[0]
        if int(np.argmax(q)) == s["best_action"]:
            correct += 1
    acc = correct / n * 100

    cce.save_model()
    if verbose:
        print(f"Corrected CCE trained for {episodes} episodes.")
        print(f"  Fit accuracy on {n} expert scenarios: {acc:.1f}%")
        print(f"  Model saved: models/cce_model.pt")
    return acc


if __name__ == "__main__":
    train_corrected()
