import numpy as np
import torch
import torch.nn as nn
from datetime import datetime


# ── RNN Model ─────────────────────────────────────────────────────────────────
class OutbreakRNN(nn.Module):
    def __init__(self, input_size=1, hidden_size=64, num_layers=2, output_size=1):
        super(OutbreakRNN, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers  = num_layers
        self.rnn = nn.RNN(
            input_size,
            hidden_size,
            num_layers,
            batch_first=True,
            nonlinearity="tanh"
        )
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x, hidden=None):
        out, hidden = self.rnn(x, hidden)
        out = self.fc(out[:, -1, :])
        return out, hidden


# ── Outbreak Trend Predictor ──────────────────────────────────────────────────
class OutbreakTrendPredictor:
    def __init__(self):
        self.device      = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model       = OutbreakRNN().to(self.device)
        self.optimizer   = torch.optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion   = nn.MSELoss()
        self.is_trained  = False
        self.case_history = []

    def add_case_record(self, cases: int):
        self.case_history.append(cases)

    def _normalize(self, data):
        data   = np.array(data, dtype=np.float32)
        max_val = max(data.max(), 1)
        return data / max_val, max_val

    def train_on_history(self, epochs=50):
        if len(self.case_history) < 4:
            return False

        data, max_val = self._normalize(self.case_history)
        self.max_val  = max_val

        X, y = [], []
        seq_len = 3
        for i in range(len(data) - seq_len):
            X.append(data[i:i + seq_len])
            y.append(data[i + seq_len])

        if not X:
            return False

        X_tensor = torch.tensor(np.array(X), dtype=torch.float32).unsqueeze(-1).to(self.device)
        y_tensor = torch.tensor(np.array(y), dtype=torch.float32).unsqueeze(-1).to(self.device)

        self.model.train()
        for epoch in range(epochs):
            self.optimizer.zero_grad()
            output, _ = self.model(X_tensor)
            loss = self.criterion(output, y_tensor)
            loss.backward()
            self.optimizer.step()

        self.is_trained = True
        return True

    def predict_next(self, days_ahead=3):
        if not self.is_trained or len(self.case_history) < 3:
            return self._simple_projection(days_ahead)

        self.model.eval()
        predictions = []
        data, max_val = self._normalize(self.case_history)
        sequence = list(data[-3:])

        with torch.no_grad():
            for _ in range(days_ahead):
                input_tensor = torch.FloatTensor(
                    sequence[-3:]
                ).unsqueeze(0).unsqueeze(-1).to(self.device)
                output, _ = self.model(input_tensor)
                next_val  = output.item()
                predictions.append(round(next_val * max_val))
                sequence.append(next_val)

        return [max(0, p) for p in predictions]

    def _simple_projection(self, days_ahead):
        if len(self.case_history) < 2:
            last = self.case_history[-1] if self.case_history else 0
            return [last] * days_ahead
        growth = []
        for i in range(1, len(self.case_history)):
            prev = self.case_history[i - 1]
            curr = self.case_history[i]
            if prev > 0:
                growth.append((curr - prev) / prev)
        avg_growth = np.mean(growth) if growth else 0.1
        projections = []
        last = self.case_history[-1]
        for _ in range(days_ahead):
            last = round(last * (1 + avg_growth))
            projections.append(max(0, last))
        return projections

    def assess_trend(self):
        if len(self.case_history) < 3:
            return "insufficient data"
        recent = self.case_history[-3:]
        if recent[-1] > recent[-2] > recent[-3]:
            rate = (recent[-1] - recent[-3]) / max(recent[-3], 1) * 100
            if rate > 50:
                return "rapidly increasing"
            return "increasing"
        elif recent[-1] < recent[-2] < recent[-3]:
            return "decreasing"
        elif abs(recent[-1] - recent[-3]) < recent[-3] * 0.05:
            return "stable"
        return "fluctuating"

    def generate_written_report(self, predictions, trend, days_ahead=3):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history   = self.case_history

        lines = []
        lines.append("OUTBREAK TREND PREDICTION UNIT")
        lines.append("Recurrent Neural Network Trend Analysis Report")
        lines.append(f"Generated: {timestamp}")
        lines.append("")

        lines.append("HISTORICAL CASE TREND")
        lines.append("")
        lines.append(
            f"  The system has recorded a total of {len(history)} data point(s) "
            f"for this outbreak. The case counts recorded are as follows:"
        )
        lines.append("")
        for i, cases in enumerate(history, 1):
            lines.append(f"  Day {i:>2}: {cases} cases")
        lines.append("")

        lines.append("TREND ASSESSMENT")
        lines.append("")
        lines.append(
            f"  Based on the historical case data, the outbreak trend has been "
            f"assessed as: {trend.upper()}."
        )
        lines.append("")
        if trend == "rapidly increasing":
            lines.append(
                f"  The outbreak is escalating at a rapid pace. Immediate and "
                f"aggressive intervention is strongly recommended to prevent "
                f"the situation from spiralling beyond the capacity of the "
                f"health system to manage."
            )
        elif trend == "increasing":
            lines.append(
                f"  The outbreak is showing a steady upward trajectory. "
                f"Response teams should intensify surveillance and intervention "
                f"activities to bring the situation under control before it "
                f"reaches a critical threshold."
            )
        elif trend == "decreasing":
            lines.append(
                f"  The outbreak appears to be declining. Current interventions "
                f"may be having a positive effect. Response teams are advised to "
                f"maintain current measures and continue monitoring closely to "
                f"ensure the trend is sustained."
            )
        elif trend == "stable":
            lines.append(
                f"  Case counts have remained relatively stable over the recent "
                f"period. While this is a positive sign, sustained vigilance is "
                f"required to prevent a resurgence."
            )
        else:
            lines.append(
                f"  Case counts are fluctuating without a clear directional "
                f"trend. Response teams should maintain heightened surveillance "
                f"and be prepared to scale up interventions rapidly if needed."
            )
        lines.append("")

        lines.append(f"PREDICTED CASE COUNTS — NEXT {days_ahead} DAYS")
        lines.append("")
        lines.append(
            f"  Based on the pattern identified in the historical case data, "
            f"the system projects the following case counts for the next "
            f"{days_ahead} day(s):"
        )
        lines.append("")
        for i, pred in enumerate(predictions, 1):
            lines.append(f"  Day {len(history) + i:>2} (Projected): {pred} cases")
        lines.append("")
        lines.append(
            f"  These projections are estimates based on observed trends and "
            f"should be interpreted alongside current field intelligence and "
            f"epidemiological assessments. Actual case counts may vary depending "
            f"on the effectiveness of ongoing interventions."
        )
        lines.append("")
        lines.append("END OF REPORT")

        return "\n".join(lines)

    def run_full_analysis(self, case_history: list, days_ahead=3):
        self.case_history = case_history
        self.train_on_history()
        predictions = self.predict_next(days_ahead)
        trend       = self.assess_trend()
        report      = self.generate_written_report(predictions, trend, days_ahead)
        return {
            "case_history":  case_history,
            "trend":         trend,
            "predictions":   predictions,
            "days_ahead":    days_ahead,
            "written_report": report
        }

# ── Movement Pattern Recognition ──────────────────────────────────────────────
class MovementPatternRecognizer:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model  = OutbreakRNN(
            input_size=1, hidden_size=64,
            num_layers=2, output_size=1
        ).to(self.device)
        self.optimizer = torch.optim.Adam(
            self.model.parameters(), lr=0.001
        )
        self.criterion = nn.MSELoss()

    def _normalize(self, data):
        data    = np.array(data, dtype=np.float32)
        max_val = max(data.max(), 1)
        return data / max_val, max_val

    def _train(self, sequence, epochs=50):
        if len(sequence) < 4:
            return False
        data, _ = self._normalize(sequence)
        X, y    = [], []
        for i in range(len(data) - 3):
            X.append(data[i:i + 3])
            y.append(data[i + 3])
        if not X:
            return False
        X_t = torch.tensor(
            np.array(X), dtype=torch.float32
        ).unsqueeze(-1).to(self.device)
        y_t = torch.tensor(
            np.array(y), dtype=torch.float32
        ).unsqueeze(-1).to(self.device)
        self.model.train()
        for _ in range(epochs):
            self.optimizer.zero_grad()
            out, _ = self.model(X_t)
            loss   = self.criterion(out, y_t)
            loss.backward()
            self.optimizer.step()
        return True

    def _predict_next(self, sequence, days=3):
        data, max_val = self._normalize(sequence)
        seq           = list(data[-3:])
        preds         = []
        self.model.eval()
        with torch.no_grad():
            for _ in range(days):
                inp = torch.tensor(
                    np.array(seq[-3:]), dtype=torch.float32
                ).unsqueeze(0).unsqueeze(-1).to(self.device)
                out, _ = self.model(inp)
                val    = out.item()
                preds.append(max(0, round(val * max_val)))
                seq.append(val)
        return preds

    def _assess_region_trend(self, cases):
        if len(cases) < 2:
            return "insufficient data"
        recent = cases[-3:] if len(cases) >= 3 else cases
        if len(recent) >= 2:
            if recent[-1] > recent[-2]:
                growth = (recent[-1] - recent[-2]) / max(recent[-2], 1) * 100
                if growth > 50:
                    return "rapidly increasing"
                return "increasing"
            elif recent[-1] < recent[-2]:
                return "decreasing"
        return "stable"

    def analyze(self, region_data: dict, days_ahead=3):
        """
        region_data format:
        {
            "Region A": [10, 25, 60, 140],
            "Region B": [5, 12, 30, 80],
            "Region C": [2, 5, 10, 18]
        }
        Each list = daily case counts for that region
        """
        results     = {}
        totals      = {}
        trends      = {}
        predictions = {}

        for region, cases in region_data.items():
            totals[region]  = sum(cases)
            trends[region]  = self._assess_region_trend(cases)
            trained = self._train(cases)
            if trained and len(cases) >= 4:
                predictions[region] = self._predict_next(cases, days_ahead)
            else:
                last   = cases[-1] if cases else 0
                growth = 0.1
                if len(cases) >= 2 and cases[-2] > 0:
                    growth = (cases[-1] - cases[-2]) / cases[-2]
                preds  = []
                val    = last
                for _ in range(days_ahead):
                    val = round(val * (1 + growth))
                    preds.append(max(0, val))
                predictions[region] = preds

            latest = cases[-1] if cases else 0
            prev   = cases[-2] if len(cases) >= 2 else 0
            results[region] = {
                "total_cases":   totals[region],
                "latest_cases":  latest,
                "previous_cases": prev,
                "trend":         trends[region],
                "predictions":   predictions[region],
                "case_history":  cases
            }

        # Identify epicentre
        epicentre = max(totals, key=totals.get)

        # Identify spreading regions
        spreading = [
            r for r, t in trends.items()
            if t in ("increasing", "rapidly increasing")
            and r != epicentre
        ]

        # Identify at-risk regions
        at_risk = [
            r for r, t in trends.items()
            if t == "stable" or t == "insufficient data"
        ]

        # Identify improving regions
        improving = [
            r for r, t in trends.items()
            if t == "decreasing"
        ]

        report = self.generate_written_report(
            results, epicentre, spreading,
            at_risk, improving, days_ahead
        )

        return {
            "regions":   results,
            "epicentre": epicentre,
            "spreading": spreading,
            "at_risk":   at_risk,
            "improving": improving,
            "written_report": report
        }

    def generate_written_report(
        self, results, epicentre,
        spreading, at_risk, improving, days_ahead
    ):
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = []
        lines.append("OUTBREAK MOVEMENT PATTERN RECOGNITION UNIT")
        lines.append("Geographic Spread Analysis Report")
        lines.append(f"Generated: {timestamp}")
        lines.append("")

        lines.append("OVERVIEW")
        lines.append("")
        lines.append(
            f"  This report presents a geographic analysis of the current "
            f"outbreak across {len(results)} region(s). The analysis examines "
            f"how the outbreak is moving between regions, identifies the "
            f"primary epicentre, and provides case count projections for "
            f"each region over the next {days_ahead} day(s)."
        )
        lines.append("")

        lines.append("EPICENTRE IDENTIFICATION")
        lines.append("")
        lines.append(
            f"  The primary outbreak epicentre has been identified as "
            f"{epicentre}, which has recorded the highest cumulative case "
            f"count of {results[epicentre]['total_cases']} cases. Response "
            f"authorities should prioritise resource deployment and "
            f"intervention activities in this region above all others."
        )
        lines.append("")

        lines.append("REGIONAL TREND ANALYSIS")
        lines.append("")
        for region, data in results.items():
            trend = data["trend"]
            lines.append(f"  {region}:")
            lines.append(
                f"  Latest recorded cases: {data['latest_cases']}. "
                f"Trend: {trend.upper()}. "
                f"Total cumulative cases: {data['total_cases']}."
            )
            lines.append("")

        if spreading:
            lines.append("ACTIVE SPREAD REGIONS")
            lines.append("")
            lines.append(
                f"  The following region(s) are showing active upward "
                f"spread and require urgent attention alongside the "
                f"primary epicentre:"
            )
            for r in spreading:
                lines.append(f"  - {r} (Trend: {results[r]['trend'].upper()})")
            lines.append("")

        if at_risk:
            lines.append("AT-RISK REGIONS")
            lines.append("")
            lines.append(
                f"  The following region(s) currently show stable or "
                f"early-stage case counts but are considered at risk of "
                f"increased spread if interventions are not put in place:"
            )
            for r in at_risk:
                lines.append(f"  - {r}")
            lines.append("")

        if improving:
            lines.append("IMPROVING REGIONS")
            lines.append("")
            lines.append(
                f"  The following region(s) are showing declining case "
                f"counts, suggesting that current interventions may be "
                f"having a positive effect:"
            )
            for r in improving:
                lines.append(f"  - {r}")
            lines.append("")

        lines.append(f"PROJECTED CASE COUNTS — NEXT {days_ahead} DAYS")
        lines.append("")
        lines.append(
            f"  Based on observed movement patterns, the following case "
            f"count projections have been generated for each region:"
        )
        lines.append("")
        for region, data in results.items():
            lines.append(f"  {region}:")
            for i, pred in enumerate(data["predictions"], 1):
                day_num = len(data["case_history"]) + i
                lines.append(f"    Day {day_num} (Projected): {pred} cases")
            lines.append("")

        lines.append("RECOMMENDATIONS")
        lines.append("")
        lines.append(
            f"  Based on the movement pattern analysis, the following "
            f"actions are recommended:"
        )
        lines.append("")
        lines.append(
            f"  1. Concentrate maximum response resources in {epicentre} "
            f"as the confirmed primary epicentre."
        )
        if spreading:
            lines.append(
                f"  2. Deploy preventive interventions immediately to "
                f"{', '.join(spreading)} to slow active spread."
            )
        if at_risk:
            lines.append(
                f"  3. Establish surveillance outposts in "
                f"{', '.join(at_risk)} to monitor for early signs "
                f"of increased transmission."
            )
        if improving:
            lines.append(
                f"  4. Maintain current interventions in "
                f"{', '.join(improving)} and monitor closely to "
                f"ensure the declining trend is sustained."
            )
        lines.append("")
        lines.append(
            f"  These recommendations should be reviewed alongside "
            f"current field intelligence and updated as new case data "
            f"becomes available."
        )
        lines.append("")
        lines.append("END OF REPORT")

        return "\n".join(lines)


# ── Quick Test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    predictor   = OutbreakTrendPredictor()
    case_history = [10, 25, 60, 140, 310, 650, 1200]

    result = predictor.run_full_analysis(case_history, days_ahead=3)

    print(result["written_report"])
    print(f"\nTrend     : {result['trend']}")
    print(f"Predicted : {result['predictions']}")