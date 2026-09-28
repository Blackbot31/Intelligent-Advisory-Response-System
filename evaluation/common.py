"""
Shared utilities for the IARMS evaluation suite.

Contains:
  - loading of the 27 expert-labelled coordination scenarios,
  - a documented synthetic scenario generator (for a held-out generalisation test),
  - the non-learning baselines (random, majority-class, rule-based),
  - metric helpers (accuracy, macro precision/recall/F1, confusion matrix).

Everything here is deterministic given a seed so results are reproducible.
"""
import sys
import os
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from training.historical_data import HISTORICAL_SCENARIOS

# Action space (index -> human label), mirrors subsystems/cce.py
ACTIONS = [
    "Deploy medical teams",
    "Increase resource allocation",
    "Issue public health advisory",
    "Activate emergency protocol",
]
N_ACTIONS = len(ACTIONS)
STATE_SIZE = 10


def load_expert_dataset():
    """Return (X, y) for the 27 expert-labelled scenarios.

    X : float array [n, 10]  -- outbreak state vectors
    y : int array   [n]      -- expert 'best_action' labels
    """
    X = np.array([s["state"] for s in HISTORICAL_SCENARIOS], dtype=np.float32)
    y = np.array([s["best_action"] for s in HISTORICAL_SCENARIOS], dtype=np.int64)
    return X, y


# ---------------------------------------------------------------------------
# Rule-based baseline / expert policy
# ---------------------------------------------------------------------------
def rule_based_action(state):
    """A transparent 4-line clinical-style heuristic over the state vector.

    state indices: [0]cases [1]deaths [2]resources [3]hospitals [4]personnel
                   [5]risk_score [6]supply_level [7]coordination [8]days [9]response
    """
    risk = state[5]
    supply = state[6]
    if risk > 0.75:
        return 3  # activate emergency protocol
    if risk > 0.55:
        return 0 if supply > 0.30 else 1  # deploy teams, or shore up supply first
    if supply < 0.35:
        return 1  # increase resource allocation
    return 2      # issue advisory


def rule_based_predict(X):
    return np.array([rule_based_action(x) for x in X], dtype=np.int64)


def random_predict(X, seed=0):
    rng = np.random.default_rng(seed)
    return rng.integers(0, N_ACTIONS, size=len(X)).astype(np.int64)


def majority_predict(X, y_train):
    vals, counts = np.unique(y_train, return_counts=True)
    maj = int(vals[np.argmax(counts)])
    return np.full(len(X), maj, dtype=np.int64)


# ---------------------------------------------------------------------------
# Synthetic scenario generator (for a held-out generalisation test)
# ---------------------------------------------------------------------------
def generate_synthetic_scenarios(n=600, seed=42, noise=0.05):
    """Generate synthetic outbreak states labelled by the expert rule.

    Method (documented for reproducibility):
      * Sample risk_score and supply_level uniformly, and derive correlated
        case/death/resource/personnel figures with mild Gaussian noise.
      * Label each state with `rule_based_action` (the expert policy).
    This gives a larger, class-balanced corpus on which a learned model must
    RECOVER the expert policy from data and GENERALISE to unseen states --
    i.e. it tests learning, not memorisation. The rule is the 'teacher'; the
    rule-based baseline therefore acts as an approximate upper bound, and the
    learned models are judged on how closely they match it out-of-sample.
    """
    rng = np.random.default_rng(seed)
    X = np.zeros((n, STATE_SIZE), dtype=np.float32)
    for i in range(n):
        risk = rng.uniform(0.05, 0.98)
        supply = rng.uniform(0.05, 0.95)
        days = rng.integers(1, 45)
        # cases/deaths grow with risk and duration
        cases = max(1, int(rng.normal(risk * 700, 60)))
        deaths = max(0, int(cases * risk * rng.uniform(0.05, 0.15)))
        hospitals = max(1, int(rng.normal(8 - risk * 6, 1)))
        personnel = max(1, int(rng.normal(50 - risk * 45, 4)))
        resources = float(np.clip(supply + rng.normal(0, noise), 0, 1))
        coordination = float(np.clip(rng.uniform(0.1, 0.9), 0, 1))
        response = float(np.clip(0.2 + risk * 0.7 + rng.normal(0, noise), 0, 1))
        X[i] = [cases, deaths, resources, hospitals, personnel,
                risk, supply, coordination, days, response]
    y = rule_based_predict(X)
    return X, y


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
def compute_metrics(y_true, y_pred):
    from sklearn.metrics import (accuracy_score, precision_score,
                                 recall_score, f1_score)
    return {
        "accuracy":  accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, average="macro", zero_division=0),
        "recall":    recall_score(y_true, y_pred, average="macro", zero_division=0),
        "f1":        f1_score(y_true, y_pred, average="macro", zero_division=0),
    }


def confusion(y_true, y_pred):
    from sklearn.metrics import confusion_matrix
    return confusion_matrix(y_true, y_pred, labels=list(range(N_ACTIONS)))
