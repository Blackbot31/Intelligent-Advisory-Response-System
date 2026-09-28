"""
Main evaluation runner for IARMS.

Produces (into evaluation/results/):
  * metrics_cv.csv          -- stratified k-fold CV metrics for every method
  * metrics_holdout.csv     -- generalisation on a large synthetic held-out set
  * rnn_metrics.csv         -- RNN forecasting vs naive baselines
  * learning_curve.png      -- CorrectedDQN greedy accuracy vs training episode
  * confusion_*.png         -- confusion matrices for the learned models
  * baseline_comparison.png -- bar chart of accuracy across all methods
  * SUMMARY.md              -- human-readable summary table

Run:  python -m evaluation.run_evaluation
Deterministic given the seeds below.
"""
import os
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from evaluation.common import (
    load_expert_dataset, generate_synthetic_scenarios,
    rule_based_predict, random_predict, majority_predict,
    compute_metrics, confusion, ACTIONS, N_ACTIONS,
)
from evaluation.models import CorrectedDQN, SupervisedCCE
from evaluation.rnn_eval import evaluate_rnn

RESULTS = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS, exist_ok=True)
SEEDS = [0, 1, 2, 3, 4]


def _mean_std(dicts):
    keys = dicts[0].keys()
    return {k: (np.mean([d[k] for d in dicts]), np.std([d[k] for d in dicts])) for k in keys}


def cross_validate(X, y, n_splits=5):
    """Stratified k-fold CV for every method, averaged over SEEDS."""
    from sklearn.model_selection import StratifiedKFold
    methods = ["Random", "Majority", "Rule-based",
               "CorrectedDQN (Route A)", "Supervised (Route B)"]
    per_method = {m: [] for m in methods}

    for seed in SEEDS:
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
        fold_metrics = {m: [] for m in methods}
        for tr, te in skf.split(X, y):
            Xtr, Xte, ytr, yte = X[tr], X[te], y[tr], y[te]

            fold_metrics["Random"].append(
                compute_metrics(yte, random_predict(Xte, seed=seed)))
            fold_metrics["Majority"].append(
                compute_metrics(yte, majority_predict(Xte, ytr)))
            fold_metrics["Rule-based"].append(
                compute_metrics(yte, rule_based_predict(Xte)))

            dqn = CorrectedDQN(seed=seed).fit(Xtr, ytr)
            fold_metrics["CorrectedDQN (Route A)"].append(
                compute_metrics(yte, dqn.predict(Xte)))

            sup = SupervisedCCE(seed=seed).fit(Xtr, ytr)
            fold_metrics["Supervised (Route B)"].append(
                compute_metrics(yte, sup.predict(Xte)))

        for m in methods:
            # average across folds for this seed
            per_method[m].append(_avg(fold_metrics[m]))

    return {m: _mean_std(per_method[m]) for m in methods}


def _avg(list_of_metric_dicts):
    keys = list_of_metric_dicts[0].keys()
    return {k: float(np.mean([d[k] for d in list_of_metric_dicts])) for k in keys}


def holdout_generalisation(Xtr, ytr):
    """Train on the 27 expert scenarios, test on a large synthetic set."""
    Xte, yte = generate_synthetic_scenarios(n=600, seed=42)
    rows = {}
    rows["Random"] = compute_metrics(yte, random_predict(Xte, seed=0))
    rows["Majority"] = compute_metrics(yte, majority_predict(Xte, ytr))
    rows["Rule-based (teacher)"] = compute_metrics(yte, rule_based_predict(Xte))

    dqn = CorrectedDQN(seed=0).fit(Xtr, ytr)
    rows["CorrectedDQN (Route A)"] = compute_metrics(yte, dqn.predict(Xte))
    sup = SupervisedCCE(seed=0).fit(Xtr, ytr)
    rows["Supervised (Route B)"] = compute_metrics(yte, sup.predict(Xte))
    return rows, (dqn, sup, Xte, yte)


def save_csv(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def plot_learning_curve(dqn, path):
    if not dqn.learning_curve:
        return
    ep, acc = zip(*dqn.learning_curve)
    plt.figure(figsize=(7, 4))
    plt.plot(ep, [a * 100 for a in acc], marker="o", ms=3)
    plt.xlabel("Training episode")
    plt.ylabel("Greedy accuracy on scenarios (%)")
    plt.title("CorrectedDQN (Route A) learning curve")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close()


def plot_confusion(cm, title, path):
    plt.figure(figsize=(5.2, 4.6))
    plt.imshow(cm, cmap="Blues")
    plt.colorbar(fraction=0.046)
    plt.xticks(range(N_ACTIONS), [a.split()[0] for a in ACTIONS], rotation=45, ha="right")
    plt.yticks(range(N_ACTIONS), [a.split()[0] for a in ACTIONS])
    thresh = cm.max() / 2 if cm.max() else 0.5
    for i in range(N_ACTIONS):
        for j in range(N_ACTIONS):
            plt.text(j, i, int(cm[i, j]), ha="center",
                     color="white" if cm[i, j] > thresh else "black")
    plt.ylabel("True action")
    plt.xlabel("Predicted action")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close()


def plot_baselines(cv, path):
    methods = list(cv.keys())
    accs = [cv[m]["accuracy"][0] * 100 for m in methods]
    errs = [cv[m]["accuracy"][1] * 100 for m in methods]
    colors = ["#bbb", "#bbb", "#f0a", "#09c", "#0a6"]
    plt.figure(figsize=(8, 4.2))
    plt.bar(range(len(methods)), accs, yerr=errs, capsize=4,
            color=colors[:len(methods)])
    plt.xticks(range(len(methods)), methods, rotation=20, ha="right")
    plt.ylabel("CV accuracy (%)")
    plt.title("Coordination action selection — accuracy by method (5-fold CV)")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close()


def main():
    X, y = load_expert_dataset()
    print(f"Loaded {len(X)} expert scenarios.")

    # 1) Cross-validated metrics ------------------------------------------------
    print("Running stratified 5-fold CV over 5 seeds...")
    cv = cross_validate(X, y, n_splits=5)
    rows = []
    for m, md in cv.items():
        rows.append([m] + [f"{md[k][0]:.3f}±{md[k][1]:.3f}"
                           for k in ["accuracy", "precision", "recall", "f1"]])
    save_csv(os.path.join(RESULTS, "metrics_cv.csv"),
             ["method", "accuracy", "precision", "recall", "f1"], rows)

    # 2) Held-out generalisation -----------------------------------------------
    print("Training on 27 scenarios, testing on 600 synthetic states...")
    holdout, (dqn_h, sup_h, Xte, yte) = holdout_generalisation(X, y)
    hrows = [[m] + [f"{md[k]:.3f}" for k in ["accuracy", "precision", "recall", "f1"]]
             for m, md in holdout.items()]
    save_csv(os.path.join(RESULTS, "metrics_holdout.csv"),
             ["method", "accuracy", "precision", "recall", "f1"], hrows)

    # 3) RNN forecasting --------------------------------------------------------
    print("Evaluating RNN forecaster...")
    rnn = evaluate_rnn(n_curves=40, length=16, horizon=3)
    rrows = [[m, f"{d['MAE']:.2f}", f"{d['RMSE']:.2f}", f"{d['MAPE']:.1f}"]
             for m, d in rnn.items() if isinstance(d, dict)]
    save_csv(os.path.join(RESULTS, "rnn_metrics.csv"),
             ["method", "MAE", "RMSE", "MAPE(%)"], rrows)

    # 4) Plots ------------------------------------------------------------------
    print("Rendering plots...")
    dqn_full = CorrectedDQN(seed=0).fit(X, y)
    plot_learning_curve(dqn_full, os.path.join(RESULTS, "learning_curve.png"))
    plot_confusion(confusion(yte, dqn_h.predict(Xte)),
                   "CorrectedDQN (Route A) — held-out",
                   os.path.join(RESULTS, "confusion_dqn.png"))
    plot_confusion(confusion(yte, sup_h.predict(Xte)),
                   "Supervised (Route B) — held-out",
                   os.path.join(RESULTS, "confusion_supervised.png"))
    plot_baselines(cv, os.path.join(RESULTS, "baseline_comparison.png"))

    # 5) Markdown summary -------------------------------------------------------
    with open(os.path.join(RESULTS, "SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("# IARMS evaluation results\n\n")
        f.write("## Coordination action selection — 5-fold CV (mean±std over 5 seeds)\n\n")
        f.write("| Method | Accuracy | Precision | Recall | F1 |\n|---|---|---|---|---|\n")
        for r in rows:
            f.write("| " + " | ".join(r) + " |\n")
        f.write("\n## Generalisation — trained on 27 expert scenarios, tested on 600 synthetic states\n\n")
        f.write("| Method | Accuracy | Precision | Recall | F1 |\n|---|---|---|---|---|\n")
        for r in hrows:
            f.write("| " + " | ".join(r) + " |\n")
        f.write("\n## RNN outbreak forecasting (40 curves, 3-day horizon)\n\n")
        f.write("| Method | MAE | RMSE | MAPE(%) |\n|---|---|---|---|\n")
        for r in rrows:
            f.write("| " + " | ".join(r) + " |\n")
    print(f"Done. Results written to {RESULTS}")


if __name__ == "__main__":
    main()
