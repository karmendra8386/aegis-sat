"""Anchor the detector layer to real ESA OPS-SAT telemetry (OPS-SAT-AD).

Dataset: OPSSAT-AD, Zenodo DOI 10.5281/zenodo.12588359, real OPS-SAT
telemetry segments labelled by ESA operations engineers. Files in
data/opssat_ad/: dataset.csv (2,123 segments with engineered features,
anomaly flag, and the dataset's own train/test split) and segments.csv
(303k labelled points from the anomalous segments).

Experiment: a deliberately simple, explainable detector — logistic
regression on eight standard segment features, trained only on the
dataset's train split, evaluated on its test split. The point is not
detector performance (dedicated AD models do better); it is that the
detection layer feeding a policy gate can be validated end-to-end on
real, expert-labelled spacecraft telemetry, and that real anomalous
segments persist for minutes — the regime our multi-step episodes and
delayed ground replies are sized for.
Outputs: results/opssat_anchor.md
"""
import csv, math, os, statistics
from collections import Counter

BASE = os.path.join(os.path.dirname(__file__), "..")
SEGFEATS = os.path.join(BASE, "data", "opssat_ad", "dataset.csv")
POINTS = os.path.join(BASE, "data", "opssat_ad", "segments.csv")
FEATURES = ["var", "std", "kurtosis", "skew", "n_peaks", "diff_peaks",
            "diff_var", "gaps_squared"]
LOG_FEATURES = {"var", "std", "diff_var", "gaps_squared", "n_peaks", "diff_peaks"}


def load():
    rows = list(csv.DictReader(open(SEGFEATS)))
    def vec(r):
        return [math.log1p(float(r[f])) if f in LOG_FEATURES else float(r[f])
                for f in FEATURES]
    train = [(vec(r), int(r["anomaly"])) for r in rows if r["train"] == "1"]
    test = [(vec(r), int(r["anomaly"])) for r in rows if r["train"] == "0"]
    return rows, train, test


def standardise(train, *sets):
    cols = list(zip(*[x for x, _ in train]))
    mu = [statistics.fmean(c) for c in cols]
    sd = [statistics.pstdev(c) or 1.0 for c in cols]
    def norm(data):
        return [([(v - mu[i]) / sd[i] for i, v in enumerate(x)], y) for x, y in data]
    return [norm(s) for s in sets]


def train_logreg(data, epochs=300, lr=0.1):
    w = [0.0] * len(FEATURES); b = 0.0
    for _ in range(epochs):
        for x, y in data:
            z = sum(wi * xi for wi, xi in zip(w, x)) + b
            p = 1 / (1 + math.exp(-max(-30, min(30, z))))
            g = p - y
            for i in range(len(w)):
                w[i] -= lr * g * x[i] / len(data)
            b -= lr * g / len(data)
    return w, b


def score(w, b, x):
    return 1 / (1 + math.exp(-max(-30, min(30, sum(wi * xi for wi, xi in zip(w, x)) + b))))


def auc(scored):
    pos = [s for s, y in scored if y == 1]; neg = [s for s, y in scored if y == 0]
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


rows, train, test = load()
train_n, test_n = standardise(train, train, test)
w, b = train_logreg(train_n)
scored = [(score(w, b, x), y) for x, y in test_n]
a = auc(scored)
thr = 0.5
tp = sum(s >= thr and y == 1 for s, y in scored)
fn = sum(s < thr and y == 1 for s, y in scored)
fp = sum(s >= thr and y == 0 for s, y in scored)
tn = sum(s < thr and y == 0 for s, y in scored)

anom_durs = [float(r["duration"]) for r in rows if r["anomaly"] == "1"]
channels = Counter(r["channel"] for r in rows)
n_points = sum(1 for _ in open(POINTS)) - 1

lines = [
    "# OPS-SAT-AD telemetry anchoring (ESA OPS-SAT, real telemetry)",
    "",
    f"- Dataset: OPSSAT-AD, Zenodo DOI 10.5281/zenodo.12588359 — "
    f"{len(rows):,} segments over {len(channels)} telemetry channels "
    f"({sum(1 for r in rows if r['anomaly']=='1')} anomalous / "
    f"{sum(1 for r in rows if r['anomaly']=='0')} nominal), plus "
    f"{n_points:,} labelled points from the anomalous segments.",
    f"- Anomalous segment duration: median {statistics.median(anom_durs):.0f}s, "
    f"max {max(anom_durs):.0f}s — real faults persist for minutes, which is "
    f"why the harness uses multi-step episodes with delayed ground replies "
    f"rather than single-shot decisions.",
    "",
    "## Simple explainable detector (logistic regression, 8 segment features)",
    "",
    f"- Trained on the dataset's train split only "
    f"({len(train)} segments), tested on its test split ({len(test)}).",
    f"- Test AUC: {a:.3f}",
    f"- At threshold 0.5: detection {tp}/{tp+fn} anomalous segments "
    f"({100*tp/(tp+fn):.0f}%), false alarms {fp}/{fp+tn} nominal "
    f"({100*fp/(fp+tn):.1f}%).",
    "",
    "Reading: a one-page, fully explainable detector already separates",
    "most expert-labelled anomalies on real telemetry. AEGIS-Sat's claim",
    "is not the detector — it is what happens after detection: policy",
    "tiers, the context-adaptive envelope, ground escalation, and the",
    "tamper-evident audit ledger.",
]
out = "\n".join(lines) + "\n"
os.makedirs(os.path.join(BASE, "results"), exist_ok=True)
open(os.path.join(BASE, "results", "opssat_anchor.md"), "w").write(out)
print(out)
