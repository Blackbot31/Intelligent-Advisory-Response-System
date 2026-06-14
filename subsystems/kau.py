import numpy as np
import random
from collections import defaultdict

# ─── Knowledge-Based Advisory Unit ──────────────────────────────────────────
class KnowledgeAdvisoryUnit:
    def __init__(self):
        self.q_table = defaultdict(lambda: np.zeros(5))
        self.learning_rate = 0.1
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995

        # Advisory actions available
        self.advisories = [
            "Issue community hygiene and sanitation advisory",
            "Recommend immediate isolation of confirmed cases",
            "Deploy vaccination teams to high-risk zones",
            "Activate contact tracing and monitoring protocol",
            "Issue travel restriction advisory for affected regions"
        ]

        # Knowledge base of outbreak scenarios and responses
        self.knowledge_base = {
            "high_transmission": [
                "Enforce strict movement restrictions in affected areas",
                "Scale up testing capacity immediately",
                "Activate emergency health worker deployment"
            ],
            "low_resources": [
                "Request international aid and medical supplies",
                "Redistribute available resources from low-risk zones",
                "Activate emergency procurement protocol"
            ],
            "early_stage": [
                "Initiate contact tracing immediately",
                "Issue public awareness advisory",
                "Set up isolation centres in affected communities"
            ],
            "critical_stage": [
                "Declare public health emergency",
                "Request military and civil defence support",
                "Activate national emergency response committee"
            ]
        }

    def get_state_key(self, state):
        # Convert continuous state to discrete key for Q-table
        risk_level = "high" if state["risk_score"] > 0.6 else "low"
        resource_level = "scarce" if state["resource_level"] < 0.4 else "adequate"
        stage = "critical" if state["days_active"] > 14 else "early"
        return f"{risk_level}_{resource_level}_{stage}"

    def select_advisory(self, state):
        state_key = self.get_state_key(state)
        if random.random() <= self.epsilon:
            action = random.randrange(len(self.advisories))
        else:
            action = np.argmax(self.q_table[state_key])
        return action

    def update_knowledge(self, state, action, reward, next_state):
        state_key = self.get_state_key(state)
        next_state_key = self.get_state_key(next_state)
        current_q = self.q_table[state_key][action]
        next_q = np.max(self.q_table[next_state_key])
        new_q = current_q + self.learning_rate * (
            reward + self.gamma * next_q - current_q
        )
        self.q_table[state_key][action] = new_q
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            
    def save_model(self, path="models/kau_qtable.json"):
        import os
        import json
        os.makedirs(os.path.dirname(path), exist_ok=True)
        serializable = {
            k: v.tolist()
            for k, v in self.q_table.items()
        }
        with open(path, "w") as f:
            json.dump({
                "q_table": serializable,
                "epsilon": self.epsilon
            }, f)

    def load_model(self, path="models/kau_qtable.json"):
        import os
        import json
        if not os.path.exists(path):
            return False
        with open(path, "r") as f:
            data = json.load(f)
        for k, v in data["q_table"].items():
            self.q_table[k] = np.array(v)
        self.epsilon = data["epsilon"]
        return True

    def get_contextual_advice(self, state):
        advisories = []
        if state["risk_score"] > 0.6:
            advisories.extend(self.knowledge_base["high_transmission"])
        if state["resource_level"] < 0.4:
            advisories.extend(self.knowledge_base["low_resources"])
        if state["days_active"] <= 14:
            advisories.extend(self.knowledge_base["early_stage"])
        else:
            advisories.extend(self.knowledge_base["critical_stage"])
        return advisories

    def generate_advisory(self, state):
        action_index     = self.select_advisory(state)
        primary_advisory = self.advisories[action_index]
        contextual_advice = self.get_contextual_advice(state)
        state_key        = self.get_state_key(state)
        result = {
            "primary_advisory":          primary_advisory,
            "contextual_recommendations": contextual_advice,
            "outbreak_stage": "Critical" if state["days_active"] > 14 else "Early",
            "risk_level":     "High" if state["risk_score"] > 0.6 else "Low",
            "resource_status": "Scarce" if state["resource_level"] < 0.4 else "Adequate",
            "state_profile":  state_key
        }
        self.save_model()
        result["written_report"] = self.generate_written_report(result)
        return result
        
    def generate_written_report(self, result):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = []
        lines.append("KNOWLEDGE-BASED ADVISORY UNIT")
        lines.append("Health Advisory Report")
        lines.append(f"Generated: {timestamp}")
        lines.append("")

        lines.append("OUTBREAK PROFILE")
        lines.append("")
        lines.append(
            f"  The current outbreak has been assessed and classified as being at a "
            f"{result['outbreak_stage']} stage. The risk level for the affected region "
            f"has been determined to be {result['risk_level']}, and the availability of "
            f"resources and medical supplies in the area is currently {result['resource_status']}. "
            f"These conditions have been used to generate the most appropriate health advisory "
            f"and supporting recommendations for this outbreak scenario."
        )
        lines.append("")

        lines.append("PRIMARY HEALTH ADVISORY")
        lines.append("")
        lines.append(
            f"  Based on the current outbreak profile, the following primary health advisory "
            f"has been issued for immediate action by all relevant health authorities and "
            f"response teams:"
        )
        lines.append("")
        lines.append(f"  {result['primary_advisory']}.")
        lines.append("")
        lines.append(
            f"  This advisory has been selected based on the specific combination of risk level, "
            f"resource availability, and outbreak stage currently observed. Health authorities "
            f"are strongly advised to implement this recommendation as a priority action and "
            f"communicate it clearly to all frontline health workers and community response teams."
        )
        lines.append("")

        lines.append("CONTEXTUAL RECOMMENDATIONS")
        lines.append("")
        lines.append(
            f"  In addition to the primary advisory above, the following contextual "
            f"recommendations have been identified based on the specific conditions of "
            f"this outbreak. These recommendations should be implemented alongside the "
            f"primary advisory to strengthen the overall response:"
        )
        lines.append("")
        for i, rec in enumerate(result["contextual_recommendations"], 1):
            lines.append(f"  {i}. {rec}.")
        lines.append("")

        lines.append("ADVISORY NOTE")
        lines.append("")
        lines.append(
            f"  The advisories contained in this report are generated by a knowledge-based "
            f"system that draws from an established outbreak response knowledge base and "
            f"continuously refines its recommendations through reinforcement learning. "
            f"Health authorities are advised to review these recommendations alongside "
            f"current field intelligence and epidemiological data before finalising "
            f"their response strategy."
        )
        lines.append("")
        lines.append("END OF REPORT")

        return "\n".join(lines)


# ─── Quick Test ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    kau = KnowledgeAdvisoryUnit()

    # Simulated outbreak scenario
    current_state = {
        "risk_score": 0.75,
        "resource_level": 0.3,
        "days_active": 18,
        "cases": 320,
        "deaths": 25
    }

    result = kau.generate_advisory(current_state)

    print("KAU Advisory Report:")
    print(f"  Outbreak Stage       : {result['outbreak_stage']}")
    print(f"  Risk Level           : {result['risk_level']}")
    print(f"  Resource Status      : {result['resource_status']}")
    print(f"  Primary Advisory     : {result['primary_advisory']}")
    print(f"  Contextual Advice    :")
    for advice in result["contextual_recommendations"]:
        print(f"    - {advice}")
    print("KAU subsystem loaded successfully!")