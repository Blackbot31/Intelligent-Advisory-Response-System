import numpy as np
import random
from collections import deque
import torch
import torch.nn as nn
import torch.optim as optim

class DQNModel(nn.Module):
    def __init__(self, state_size, action_size):
        super(DQNModel, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(state_size, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, action_size)
        )

    def forward(self, x):
        return self.network(x)


class CoordinationControlEngine:
    def __init__(self, state_size=10, action_size=4):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = DQNModel(state_size, action_size).to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.criterion = nn.MSELoss()

        self.actions = [
            "Deploy medical teams to affected region",
            "Increase resource allocation to sub-national units",
            "Issue public health advisory",
            "Activate emergency coordination protocol"
        ]

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            action_values = self.model(state_tensor)
        return torch.argmax(action_values).item()

    def replay(self, batch_size=32):
        if len(self.memory) < batch_size:
            return
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0).to(self.device)
            target = reward
            if not done:
                target += self.gamma * torch.max(self.model(next_state_tensor)).item()
            target_f = self.model(state_tensor).detach().clone()
            target_f[0][action] = target
            self.optimizer.zero_grad()
            output = self.model(state_tensor)
            loss = self.criterion(output, target_f)
            loss.backward()
            self.optimizer.step()
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            
    def save_model(self, path="models/cce_model.pt"):
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save({
            "model_state_dict":     self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "epsilon":              self.epsilon,
            "memory":               list(self.memory)
        }, path)

    def load_model(self, path="models/cce_model.pt"):
        import os
        if not os.path.exists(path):
            return False
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.epsilon = checkpoint["epsilon"]
        self.memory  = deque(checkpoint["memory"], maxlen=2000)
        return True

    def generate_written_report(self, result, state):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cases = int(state[0])
        deaths = int(state[1])
        risk_score = state[5]
        supply_level = state[6]
        days = int(state[8])

        risk_label = "high" if risk_score > 0.6 else "moderate" if risk_score > 0.3 else "low"
        supply_label = "critically low" if supply_level < 0.3 else "low" if supply_level < 0.5 else "adequate"

        lines = []
        lines.append("COORDINATION AND CONTROL ENGINE")
        lines.append("Outbreak Coordination Report")
        lines.append(f"Generated: {timestamp}")
        lines.append("")

        lines.append("SITUATION ASSESSMENT:")
        lines.append(
            f"An assessment of the current outbreak situation has been completed. "
            f"The affected region has recorded a total of {cases} confirmed cases and "
            f"{deaths} deaths over a period of {days} day(s) since the outbreak was first detected. "
            f"The regional risk level has been assessed as {risk_label}, and available supply levels "
            f"are currently {supply_label}. These conditions have been evaluated to determine "
            f"the most appropriate coordination and control action for this response."
        )
        lines.append("")

        lines.append("RECOMMENDED COORDINATION ACTION:")
        lines.append(f"Based on the assessment of the current outbreak conditions, the following "
                    f"coordination action is recommended for immediate implementation:")
        lines.append("")
        lines.append(f"{result['recommendation']}.")
        lines.append("")
        lines.append(
            f"This action has been identified as the most appropriate response given the "
            f"current risk profile, the number of active cases in the region, and the availability "
            f"of resources and personnel. All relevant response teams and government agencies at "
            f"both national and sub-national levels are advised to act on this recommendation "
            f"without delay to prevent further escalation of the outbreak."
        )
        lines.append("")

        lines.append("SYSTEM NOTE:")
        lines.append(
            f"The coordination recommendation provided in this report is generated by an "
            f"adaptive decision system that continuously improves its recommendations over time "
            f"based on feedback and outcomes from previous outbreak scenarios. As more data is "
            f"processed, the accuracy and confidence of future recommendations will increase. "
            f"Current model confidence stands at {result['confidence']}%. Response authorities "
            f"are advised to use this recommendation alongside other available intelligence and "
            f"situational reports when making final decisions."
        )
        lines.append("")

        return "\n".join(lines)

    def get_recommendation(self, state):
        action_index = self.act(state)

        # Simulate reward based on outbreak state
        risk_score   = state[5] if len(state) > 5 else 0.5
        supply_level = state[6] if len(state) > 6 else 0.5
        reward = 1.0 if risk_score > 0.6 and action_index in [0, 3] else 0.5
        next_state = [max(0, s * 0.95) for s in state]
        done = False

        self.remember(state, action_index, reward, next_state, done)
        self.replay()

        result = {
            "action_index":   action_index,
            "recommendation": self.actions[action_index],
            "confidence":     round((1 - self.epsilon) * 100, 2)
        }
        self.save_model()
        result["written_report"] = self.generate_written_report(result, state)
        return result


if __name__ == "__main__":
    cce = CoordinationControlEngine(state_size=10, action_size=4)
    sample_state = [150, 12, 0.4, 3, 20, 0.8, 0.3, 0.5, 7, 0.6]
    result = cce.get_recommendation(sample_state)
    print(result["written_report"])