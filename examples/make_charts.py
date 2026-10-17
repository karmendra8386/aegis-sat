"""Charts for the harness results: outcomes by setup, unsafe by scenario."""
import csv, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.join(os.path.dirname(__file__), "..")
rows = list(csv.DictReader(open(os.path.join(BASE, "results", "eval_results.csv"))))
OUT = os.path.join(BASE, "results", "charts")
os.makedirs(OUT, exist_ok=True)

NAMES = {"fdir": "A · FDIR", "unguarded": "B · Unguarded", "guarded": "C · Guarded"}
SETUPS = ["fdir", "unguarded", "guarded"]
OUTCOMES = [("full_recovery_pct", "Full recovery", "#2e7d32"),
            ("safe_recovery_pct", "Safe recovery", "#7cb342"),
            ("survived_pct", "Survived only", "#f9a825"),
            ("lost_pct", "Lost", "#c62828")]

# ---- chart 1: stacked outcomes per setup (episode-weighted across scenarios)
fig, ax = plt.subplots(figsize=(7, 4))
x = range(len(SETUPS))
bottom = [0.0] * len(SETUPS)
for key, label, color in OUTCOMES:
    vals = []
    for s in SETUPS:
        r = [row for row in rows if row["setup"] == s]
        vals.append(sum(float(row[key]) for row in r) / len(r))
    ax.bar(x, vals, bottom=bottom, label=label, color=color)
    bottom = [b + v for b, v in zip(bottom, vals)]
ax.set_xticks(list(x)); ax.set_xticklabels([NAMES[s] for s in SETUPS])
ax.set_ylabel("% of episodes"); ax.set_ylim(0, 100)
ax.set_title("Episode outcomes by setup (N=100 × 6 scenarios)")
ax.legend()
fig.tight_layout(); fig.savefig(os.path.join(OUT, "outcomes_by_setup.png"), dpi=150)

# ---- chart 2: unsafe executions per scenario (unguarded vs guarded)
scen = sorted({row["scenario"] for row in rows})
fig, ax = plt.subplots(figsize=(8, 4))
w = 0.38
for i, s in enumerate(["unguarded", "guarded"]):
    vals = [next(int(row["unsafe_executed"]) for row in rows
                 if row["setup"] == s and row["scenario"] == sc) for sc in scen]
    ax.bar([j + (i - 0.5) * w for j in range(len(scen))], vals, width=w,
           label=NAMES[s], color="#c62828" if s == "unguarded" else "#2e7d32")
ax.set_xticks(range(len(scen)))
ax.set_xticklabels([sc.replace("_", "\n") for sc in scen], fontsize=8)
ax.set_ylabel("Unsafe actions executed")
ax.set_title("Unsafe actions executed by scenario (100 episodes each)")
ax.legend()
fig.tight_layout(); fig.savefig(os.path.join(OUT, "unsafe_by_scenario.png"), dpi=150)
print("charts written to", OUT)
