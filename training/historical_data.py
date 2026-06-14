import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from subsystems.cce import CoordinationControlEngine
from subsystems.kau import KnowledgeAdvisoryUnit

# ── Historical Outbreak Scenarios ─────────────────────────────────────────────
# Each scenario contains:
# state: [cases, deaths, resources, hospitals, personnel,
#         risk_score, supply_level, coordination_score,
#         days_active, response_level]
# best_action: 0=deploy medical teams, 1=increase resources,
#              2=issue advisory, 3=activate emergency protocol
# reward: how good the action was

HISTORICAL_SCENARIOS = [

    # ── EARLY STAGE LOW RISK ──────────────────────────────────────────────────
    {
        "label":       "Early stage — low risk — adequate supply",
        "state":       [15,  1, 0.7, 5, 30, 0.2, 0.8, 0.7, 3,  0.3],
        "best_action": 2,
        "reward":      1.0,
        "disease":     "Cholera",
        "kau_state": {
            "risk_score": 0.2, "resource_level": 0.8,
            "days_active": 3,  "cases": 15, "deaths": 1
        }
    },
    {
        "label":       "Early stage — low risk — good coordination",
        "state":       [20,  2, 0.8, 6, 35, 0.25, 0.75, 0.8, 5, 0.4],
        "best_action": 2,
        "reward":      1.0,
        "disease":     "Mpox",
        "kau_state": {
            "risk_score": 0.25, "resource_level": 0.75,
            "days_active": 5,   "cases": 20, "deaths": 2
        }
    },
    {
        "label":       "Early stage — moderate risk — adequate supply",
        "state":       [45,  3, 0.6, 4, 25, 0.4, 0.65, 0.6, 7, 0.4],
        "best_action": 2,
        "reward":      0.9,
        "disease":     "COVID-19",
        "kau_state": {
            "risk_score": 0.4, "resource_level": 0.65,
            "days_active": 7,  "cases": 45, "deaths": 3
        }
    },

    # ── MODERATE STAGE ────────────────────────────────────────────────────────
    {
        "label":       "Moderate stage — medium risk — low supply",
        "state":       [80,  6, 0.4, 3, 20, 0.5, 0.35, 0.5, 10, 0.5],
        "best_action": 1,
        "reward":      1.0,
        "disease":     "Cholera",
        "kau_state": {
            "risk_score": 0.5, "resource_level": 0.35,
            "days_active": 10, "cases": 80, "deaths": 6
        }
    },
    {
        "label":       "Moderate stage — medium risk — deploy teams",
        "state":       [100, 8, 0.4, 3, 18, 0.55, 0.4, 0.45, 11, 0.5],
        "best_action": 0,
        "reward":      1.0,
        "disease":     "Mpox",
        "kau_state": {
            "risk_score": 0.55, "resource_level": 0.4,
            "days_active": 11,  "cases": 100, "deaths": 8
        }
    },
    {
        "label":       "Moderate stage — rising risk — resource scarce",
        "state":       [120, 10, 0.35, 3, 15, 0.58, 0.3, 0.4, 12, 0.5],
        "best_action": 1,
        "reward":      1.0,
        "disease":     "COVID-19",
        "kau_state": {
            "risk_score": 0.58, "resource_level": 0.3,
            "days_active": 12,  "cases": 120, "deaths": 10
        }
    },
    {
        "label":       "Moderate stage — coordination needed",
        "state":       [150, 12, 0.35, 2, 15, 0.6, 0.32, 0.35, 13, 0.5],
        "best_action": 3,
        "reward":      0.9,
        "disease":     "Ebola",
        "kau_state": {
            "risk_score": 0.6, "resource_level": 0.32,
            "days_active": 13, "cases": 150, "deaths": 12
        }
    },

    # ── HIGH RISK STAGE ───────────────────────────────────────────────────────
    {
        "label":       "High risk — deploy teams urgently",
        "state":       [200, 18, 0.3, 2, 12, 0.7, 0.25, 0.3, 16, 0.6],
        "best_action": 0,
        "reward":      1.0,
        "disease":     "Ebola",
        "kau_state": {
            "risk_score": 0.7, "resource_level": 0.25,
            "days_active": 16, "cases": 200, "deaths": 18
        }
    },
    {
        "label":       "High risk — increase sub-national resources",
        "state":       [240, 22, 0.28, 2, 10, 0.72, 0.22, 0.28, 17, 0.6],
        "best_action": 1,
        "reward":      1.0,
        "disease":     "Cholera",
        "kau_state": {
            "risk_score": 0.72, "resource_level": 0.22,
            "days_active": 17,  "cases": 240, "deaths": 22
        }
    },
    {
        "label":       "High risk — emergency protocol needed",
        "state":       [280, 26, 0.25, 2, 10, 0.75, 0.2, 0.25, 18, 0.65],
        "best_action": 3,
        "reward":      1.0,
        "disease":     "Mpox",
        "kau_state": {
            "risk_score": 0.75, "resource_level": 0.2,
            "days_active": 18,  "cases": 280, "deaths": 26
        }
    },
    {
        "label":       "High risk — advisory and teams",
        "state":       [300, 28, 0.22, 2, 8, 0.78, 0.18, 0.22, 19, 0.65],
        "best_action": 0,
        "reward":      0.9,
        "disease":     "COVID-19",
        "kau_state": {
            "risk_score": 0.78, "resource_level": 0.18,
            "days_active": 19,  "cases": 300, "deaths": 28
        }
    },

    # ── CRITICAL STAGE ────────────────────────────────────────────────────────
    {
        "label":       "Critical — activate emergency protocol",
        "state":       [400, 38, 0.18, 1, 6, 0.85, 0.15, 0.18, 22, 0.7],
        "best_action": 3,
        "reward":      1.0,
        "disease":     "Ebola",
        "kau_state": {
            "risk_score": 0.85, "resource_level": 0.15,
            "days_active": 22,  "cases": 400, "deaths": 38
        }
    },
    {
        "label":       "Critical — deploy teams and emergency protocol",
        "state":       [500, 50, 0.15, 1, 5, 0.88, 0.12, 0.15, 25, 0.75],
        "best_action": 3,
        "reward":      1.0,
        "disease":     "Cholera",
        "kau_state": {
            "risk_score": 0.88, "resource_level": 0.12,
            "days_active": 25,  "cases": 500, "deaths": 50
        }
    },
    {
        "label":       "Critical — maximum response needed",
        "state":       [650, 65, 0.12, 1, 4, 0.92, 0.1, 0.12, 28, 0.8],
        "best_action": 3,
        "reward":      1.0,
        "disease":     "COVID-19",
        "kau_state": {
            "risk_score": 0.92, "resource_level": 0.1,
            "days_active": 28,  "cases": 650, "deaths": 65
        }
    },
    {
        "label":       "Critical — Ebola maximum emergency",
        "state":       [800, 90, 0.1, 1, 3, 0.95, 0.08, 0.1, 32, 0.85],
        "best_action": 3,
        "reward":      1.0,
        "disease":     "Ebola",
        "kau_state": {
            "risk_score": 0.95, "resource_level": 0.08,
            "days_active": 32,  "cases": 800, "deaths": 90
        }
    },

    # ── DECLINING STAGE ───────────────────────────────────────────────────────
    {
        "label":       "Declining — maintain advisory",
        "state":       [180, 14, 0.55, 4, 22, 0.45, 0.6, 0.65, 20, 0.7],
        "best_action": 2,
        "reward":      1.0,
        "disease":     "Mpox",
        "kau_state": {
            "risk_score": 0.45, "resource_level": 0.6,
            "days_active": 20,  "cases": 180, "deaths": 14
        }
    },
    {
        "label":       "Declining — reduce deployment gradually",
        "state":       [140, 10, 0.6, 4, 25, 0.38, 0.65, 0.7, 22, 0.75],
        "best_action": 2,
        "reward":      1.0,
        "disease":     "Cholera",
        "kau_state": {
            "risk_score": 0.38, "resource_level": 0.65,
            "days_active": 22,  "cases": 140, "deaths": 10
        }
    },
    {
        "label":       "Recovering — issue final advisory",
        "state":       [90,  6, 0.7, 5, 28, 0.3, 0.72, 0.75, 25, 0.8],
        "best_action": 2,
        "reward":      1.0,
        "disease":     "COVID-19",
        "kau_state": {
            "risk_score": 0.3, "resource_level": 0.72,
            "days_active": 25, "cases": 90, "deaths": 6
        }
    },

    # ── RESOURCE SCARCE SCENARIOS ─────────────────────────────────────────────
    {
        "label":       "Resource scarce — early stage",
        "state":       [30,  2, 0.3, 2, 12, 0.35, 0.2, 0.4, 5, 0.4],
        "best_action": 1,
        "reward":      1.0,
        "disease":     "Mpox",
        "kau_state": {
            "risk_score": 0.35, "resource_level": 0.2,
            "days_active": 5,   "cases": 30, "deaths": 2
        }
    },
    {
        "label":       "Resource scarce — moderate stage",
        "state":       [110, 9, 0.28, 2, 10, 0.55, 0.18, 0.3, 14, 0.55],
        "best_action": 1,
        "reward":      1.0,
        "disease":     "Cholera",
        "kau_state": {
            "risk_score": 0.55, "resource_level": 0.18,
            "days_active": 14,  "cases": 110, "deaths": 9
        }
    },
    {
        "label":       "Resource scarce — high risk",
        "state":       [350, 32, 0.15, 1, 6, 0.82, 0.12, 0.2, 21, 0.7],
        "best_action": 3,
        "reward":      1.0,
        "disease":     "Ebola",
        "kau_state": {
            "risk_score": 0.82, "resource_level": 0.12,
            "days_active": 21,  "cases": 350, "deaths": 32
        }
    },

    # ── WELL COORDINATED SCENARIOS ────────────────────────────────────────────
    {
        "label":       "Well coordinated — early containment",
        "state":       [25,  1, 0.8, 6, 40, 0.3, 0.85, 0.9, 4, 0.5],
        "best_action": 2,
        "reward":      1.0,
        "disease":     "COVID-19",
        "kau_state": {
            "risk_score": 0.3, "resource_level": 0.85,
            "days_active": 4,  "cases": 25, "deaths": 1
        }
    },
    {
        "label":       "Well coordinated — moderate response",
        "state":       [95,  7, 0.65, 5, 30, 0.5, 0.7, 0.85, 12, 0.65],
        "best_action": 0,
        "reward":      1.0,
        "disease":     "Mpox",
        "kau_state": {
            "risk_score": 0.5, "resource_level": 0.7,
            "days_active": 12, "cases": 95, "deaths": 7
        }
    },
    {
        "label":       "Well coordinated — high risk but good supply",
        "state":       [260, 20, 0.55, 3, 20, 0.72, 0.6, 0.8, 18, 0.7],
        "best_action": 0,
        "reward":      1.0,
        "disease":     "Cholera",
        "kau_state": {
            "risk_score": 0.72, "resource_level": 0.6,
            "days_active": 18,  "cases": 260, "deaths": 20
        }
    },

    # ── EDGE CASES ────────────────────────────────────────────────────────────
    {
        "label":       "Very early — single case",
        "state":       [1, 0, 0.9, 8, 50, 0.1, 0.95, 0.9, 1, 0.2],
        "best_action": 2,
        "reward":      1.0,
        "disease":     "Ebola",
        "kau_state": {
            "risk_score": 0.1, "resource_level": 0.95,
            "days_active": 1,  "cases": 1, "deaths": 0
        }
    },
    {
        "label":       "Massive outbreak — extreme emergency",
        "state":       [1200, 130, 0.05, 1, 2, 0.98, 0.05, 0.08, 45, 0.9],
        "best_action": 3,
        "reward":      1.0,
        "disease":     "COVID-19",
        "kau_state": {
            "risk_score": 0.98, "resource_level": 0.05,
            "days_active": 45,  "cases": 1200, "deaths": 130
        }
    },
    {
        "label":       "Moderate cases but very high fatality",
        "state":       [55, 25, 0.4, 2, 15, 0.85, 0.3, 0.35, 8, 0.6],
        "best_action": 3,
        "reward":      1.0,
        "disease":     "Ebola",
        "kau_state": {
            "risk_score": 0.85, "resource_level": 0.3,
            "days_active": 8,   "cases": 55, "deaths": 25
        }
    }
]


def train_cce(cce, scenarios, epochs=10):
    print(f"\nTraining CCE on {len(scenarios)} scenarios "
          f"for {epochs} epochs...")
    total = 0
    for epoch in range(epochs):
        for scenario in scenarios:
            state      = scenario["state"]
            action     = scenario["best_action"]
            reward     = scenario["reward"]
            next_state = [max(0, s * 0.95) for s in state]
            done       = False
            cce.remember(state, action, reward, next_state, done)
            total += 1
        cce.replay(batch_size=16)

    # Run extra replay passes to accelerate learning
    for _ in range(50):
        cce.replay(batch_size=min(32, len(cce.memory)))

    cce.save_model()
    print(f"  CCE trained on {total} experiences")
    print(f"  Memory size  : {len(cce.memory)}")
    print(f"  Epsilon      : {round(cce.epsilon, 4)}")
    print(f"  Confidence   : {round((1 - cce.epsilon) * 100, 2)}%")
    print(f"  Model saved  : models/cce_model.pt")


def train_kau(kau, scenarios, epochs=20):
    print(f"\nTraining KAU on {len(scenarios)} scenarios "
          f"for {epochs} epochs...")
    total = 0
    for epoch in range(epochs):
        for scenario in scenarios:
            state      = scenario["kau_state"]
            action     = kau.select_advisory(state)
            reward     = scenario["reward"]
            next_state = {
                "risk_score":     max(0, state["risk_score"] - 0.05),
                "resource_level": min(1, state["resource_level"] + 0.05),
                "days_active":    state["days_active"] + 1,
                "cases":          state["cases"],
                "deaths":         state["deaths"]
            }
            kau.update_knowledge(state, action, reward, next_state)
            total += 1

    kau.save_model()
    print(f"  KAU trained on {total} experiences")
    print(f"  States learned: {len(kau.q_table)}")
    print(f"  Epsilon       : {round(kau.epsilon, 4)}")
    print(f"  Model saved   : models/kau_qtable.json")


if __name__ == "__main__":
    print("=" * 55)
    print("  IARMS — HISTORICAL DATA TRAINING")
    print("=" * 55)
    print(f"  Total scenarios: {len(HISTORICAL_SCENARIOS)}")
    print(f"  Diseases covered: Cholera, Mpox, Ebola, COVID-19")
    print(f"  Stages covered  : Early, Moderate, High, Critical,")
    print(f"                    Declining, Resource Scarce,")
    print(f"                    Well Coordinated, Edge Cases")

    cce = CoordinationControlEngine(state_size=10, action_size=4)
    kau = KnowledgeAdvisoryUnit()

    train_cce(cce, HISTORICAL_SCENARIOS, epochs=10)
    train_kau(kau, HISTORICAL_SCENARIOS, epochs=20)

    print("\n" + "=" * 55)
    print("  TRAINING COMPLETE")
    print("  Models saved and ready for use")
    print("=" * 55)