"""Run the evaluation harness and write results.

Outputs: results/eval_results.csv, results/eval_summary.md
Harness numbers only (behaviour-model agent) — NOT paper results.
Week 3: multi-step episodes, delayed ground replies, refined outcomes.
"""
import csv, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from aegis_sat.eval import run_all, SETUPS, SCENARIOS

BASE = os.path.join(os.path.dirname(__file__), "..")
N = int(sys.argv[1]) if len(sys.argv) > 1 else 100
eps = run_all(os.path.join(BASE, "policies", "fault_response.yaml"), n=N)

os.makedirs(os.path.join(BASE, "results"), exist_ok=True)
with open(os.path.join(BASE, "results", "eval_results.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["setup", "scenario", "episodes", "unsafe_executed",
                "full_recovery_pct", "safe_recovery_pct", "survived_pct", "lost_pct",
                "avg_time_to_recover", "escalations", "esc_approved", "esc_denied"])
    for setup in SETUPS:
        for scen in SCENARIOS:
            r = [e for e in eps if e.setup == setup and e.scenario == scen]
            pct = lambda outcome: f"{100*sum(e.outcome==outcome for e in r)/len(r):.0f}"
            w.writerow([setup, scen, len(r), sum(e.unsafe_executed for e in r),
                        pct("full_recovery"), pct("safe_recovery"),
                        pct("survived"), pct("lost"),
                        f"{sum(e.time_to_recover for e in r)/len(r):.1f}",
                        sum(e.escalations for e in r),
                        sum(e.escalations_approved for e in r),
                        sum(e.escalations_denied for e in r)])

agg = {}
for setup in SETUPS:
    rows = [e for e in eps if e.setup == setup]
    agg[setup] = dict(
        unsafe=sum(e.unsafe_executed for e in rows),
        full=100 * sum(e.outcome == "full_recovery" for e in rows) / len(rows),
        safe=100 * sum(e.outcome == "safe_recovery" for e in rows) / len(rows),
        surv=100 * sum(e.outcome == "survived" for e in rows) / len(rows),
        lost=100 * sum(e.outcome == "lost" for e in rows) / len(rows),
        esc=sum(e.escalations for e in rows),
        appr=sum(e.escalations_approved for e in rows),
        den=sum(e.escalations_denied for e in rows),
    )

lines = [f"# Eval summary — harness run, N={N} per scenario per setup (Week 3 model)",
         "",
         "| Setup | Unsafe executed | Full recovery % | Safe recovery % | Survived % | Lost % | Escalations (approved/denied) |",
         "|---|---|---|---|---|---|---|"]
names = {"fdir": "A · Rule-only FDIR", "unguarded": "B · Unguarded agent", "guarded": "C · Guarded agent (AEGIS-Sat)"}
for s in SETUPS:
    a = agg[s]
    lines.append(f"| {names[s]} | {a['unsafe']} | {a['full']:.0f}% | {a['safe']:.0f}% | {a['surv']:.0f}% | {a['lost']:.0f}% | {a['esc']} ({a['appr']}/{a['den']}) |")
lines += ["", "Harness validation only (behaviour-model agent, seeded, delayed ground-reply model). Not paper results."]
open(os.path.join(BASE, "results", "eval_summary.md"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
