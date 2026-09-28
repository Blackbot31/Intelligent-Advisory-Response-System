# IARMS evaluation results

## Coordination action selection — 5-fold CV (mean±std over 5 seeds)

| Method | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| Random | 0.244±0.131 | 0.161±0.076 | 0.245±0.083 | 0.181±0.075 |
| Majority | 0.253±0.000 | 0.063±0.000 | 0.250±0.000 | 0.100±0.000 |
| Rule-based | 0.741±0.009 | 0.633±0.019 | 0.700±0.000 | 0.646±0.009 |
| CorrectedDQN (Route A) | 0.428±0.078 | 0.301±0.065 | 0.370±0.087 | 0.311±0.063 |
| Supervised (Route B) | 0.436±0.042 | 0.337±0.061 | 0.355±0.048 | 0.326±0.049 |

## Generalisation — trained on 27 expert scenarios, tested on 600 synthetic states

| Method | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| Random | 0.248 | 0.247 | 0.251 | 0.243 |
| Majority | 0.227 | 0.057 | 0.250 | 0.092 |
| Rule-based (teacher) | 1.000 | 1.000 | 1.000 | 1.000 |
| CorrectedDQN (Route A) | 0.528 | 0.435 | 0.462 | 0.376 |
| Supervised (Route B) | 0.518 | 0.462 | 0.537 | 0.469 |

## RNN outbreak forecasting (40 curves, 3-day horizon)

| Method | MAE | RMSE | MAPE(%) |
|---|---|---|---|
| RNN (subsystems/rnn.py) | 199.37 | 208.64 | 25.3 |
| Last-value baseline | 48.51 | 53.44 | 6.4 |
| Linear-growth baseline | 76.01 | 82.00 | 9.0 |
