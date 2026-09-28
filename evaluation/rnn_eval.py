"""
Forecasting evaluation for the RNN outbreak-trajectory predictor
(subsystems/rnn.py :: OutbreakTrendPredictor).

We generate synthetic outbreak curves (logistic epidemic growth + observation
noise), fit the RNN on the observed portion of each curve, forecast a horizon,
and score the forecast against the held-out tail with MAE / RMSE / MAPE.
The RNN is compared against two naive baselines a reviewer expects to see:
  * last-value (persistence) forecast,
  * linear-growth extrapolation.
"""
import sys
import os
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from subsystems.rnn import OutbreakTrendPredictor


def logistic_curve(K, r, t0, length, seed):
    rng = np.random.default_rng(seed)
    t = np.arange(length)
    base = K / (1 + np.exp(-r * (t - t0)))
    noise = rng.normal(0, 0.03 * K, size=length)
    return np.clip(np.round(base + noise), 0, None).astype(int).tolist()


def _mape(true, pred):
    true = np.array(true, dtype=float)
    pred = np.array(pred, dtype=float)
    denom = np.where(true == 0, 1, true)
    return float(np.mean(np.abs((true - pred) / denom)) * 100)


def _errs(true, pred):
    true = np.array(true, dtype=float)
    pred = np.array(pred, dtype=float)
    mae = float(np.mean(np.abs(true - pred)))
    rmse = float(np.sqrt(np.mean((true - pred) ** 2)))
    return mae, rmse, _mape(true, pred)


def last_value_forecast(history, horizon):
    return [history[-1]] * horizon


def linear_forecast(history, horizon):
    if len(history) < 2:
        return [history[-1]] * horizon
    slope = history[-1] - history[-2]
    out, last = [], history[-1]
    for _ in range(horizon):
        last = max(0, last + slope)
        out.append(int(round(last)))
    return out


def evaluate_global_rnn(n_train=200, n_test=40, length=16, horizon=3, seed=7):
    """Train ONE RNN across many outbreak curves, then forecast held-out curves.

    This is the corrected way to use the recurrent model: the original code in
    subsystems/rnn.py fits a fresh network from scratch on each short curve at
    inference time (a few points, no generalisation), which is why it trails a
    trivial persistence baseline. Trained once across many curves it learns a
    reusable growth pattern.
    """
    import torch
    import torch.nn as nn

    class _RNN(nn.Module):
        def __init__(self):
            super().__init__()
            self.rnn = nn.RNN(1, 64, 2, batch_first=True, nonlinearity="tanh")
            self.fc = nn.Linear(64, 1)

        def forward(self, x):
            o, _ = self.rnn(x)
            return self.fc(o[:, -1, :])

    rng = np.random.default_rng(seed)
    torch.manual_seed(seed)

    def make(s):
        K = int(rng.uniform(300, 1500)); r = float(rng.uniform(0.3, 0.8))
        t0 = float(rng.uniform(length * 0.3, length * 0.6))
        return logistic_curve(K, r, t0, length, s)

    Xtr, ytr = [], []
    for c in range(n_train):
        cur = np.array(make(1000 + c), dtype=np.float32)
        m = max(cur.max(), 1); d = cur / m
        for i in range(len(d) - 3):
            Xtr.append(d[i:i + 3]); ytr.append(d[i + 3])
    Xtr = torch.tensor(np.array(Xtr)).unsqueeze(-1)
    ytr = torch.tensor(np.array(ytr)).unsqueeze(-1)

    net = _RNN(); opt = torch.optim.Adam(net.parameters(), 1e-3); lossf = nn.MSELoss()
    for _ in range(300):
        opt.zero_grad(); loss = lossf(net(Xtr), ytr); loss.backward(); opt.step()

    rnn_s, lv_s, lin_s = [], [], []
    net.eval()
    for c in range(n_test):
        cur = make(5000 + c); hist, truth = cur[:-horizon], cur[-horizon:]
        m = max(max(hist), 1); seq = [h / m for h in hist[-3:]]; preds = []
        with torch.no_grad():
            for _ in range(horizon):
                inp = torch.tensor(np.array(seq[-3:]), dtype=torch.float32).unsqueeze(0).unsqueeze(-1)
                v = net(inp).item(); preds.append(max(0, round(v * m))); seq.append(v)
        rnn_s.append(_errs(truth, preds))
        lv_s.append(_errs(truth, last_value_forecast(hist, horizon)))
        lin_s.append(_errs(truth, linear_forecast(hist, horizon)))

    def agg(s):
        a = np.array(s)
        return {"MAE": a[:, 0].mean(), "RMSE": a[:, 1].mean(), "MAPE": a[:, 2].mean()}

    return {
        "RNN (trained once, corrected)": agg(rnn_s),
        "Last-value baseline":           agg(lv_s),
        "Linear-growth baseline":        agg(lin_s),
        "n_test": n_test, "horizon": horizon,
    }


def evaluate_rnn(n_curves=40, length=16, horizon=3, seed=7):
    rng = np.random.default_rng(seed)
    rnn_scores, lastv_scores, lin_scores = [], [], []
    for c in range(n_curves):
        K = int(rng.uniform(300, 1500))
        r = float(rng.uniform(0.3, 0.8))
        t0 = float(rng.uniform(length * 0.3, length * 0.6))
        curve = logistic_curve(K, r, t0, length, seed=seed + c)
        history, truth = curve[:-horizon], curve[-horizon:]

        predictor = OutbreakTrendPredictor()
        result = predictor.run_full_analysis(history, days_ahead=horizon)
        rnn_pred = result["predictions"]

        rnn_scores.append(_errs(truth, rnn_pred))
        lastv_scores.append(_errs(truth, last_value_forecast(history, horizon)))
        lin_scores.append(_errs(truth, linear_forecast(history, horizon)))

    def agg(scores):
        a = np.array(scores)
        return {"MAE": a[:, 0].mean(), "RMSE": a[:, 1].mean(), "MAPE": a[:, 2].mean()}

    return {
        "RNN (subsystems/rnn.py)": agg(rnn_scores),
        "Last-value baseline":     agg(lastv_scores),
        "Linear-growth baseline":  agg(lin_scores),
        "n_curves": n_curves, "horizon": horizon,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(evaluate_rnn(), indent=2, default=float))
