# AEGIS-Sat

**Autonomous Execution with Guardrails and Interlocks for Satellites**

A policy-gated AI agent framework for safe onboard fault response.

An AI agent *proposes* fault-recovery actions. A deterministic policy gate —
readable YAML, written and signed by operators — decides what may actually
happen: **AUTO**, **AUTO+LOG**, **ESCALATE** (hold safe, ask the ground), or
**DENY**. The gate's tiers adapt to context (comms blackout, eclipse, power
margin): the *context-adaptive autonomy envelope*. Every proposal and decision
is written to a tamper-evident audit ledger.

> Research prototype. Simulation only — not flight software.

## Layout
```
src/aegis_sat/   sim.py (CubeSat simulator) · guard.py (policy gate) ·
                 agent.py (proposers) · ledger.py (audit chain)
policies/        fault_response.yaml — the gate-policy list (operator-owned)
scenarios/       6 fault-injection scenarios
examples/        demo_run.py — guarded vs unguarded smoke run
tests/           pytest suite for sim, gate, ledger
```

## Quick start
```bash
python3 -m venv .venv && .venv/bin/pip install pytest pyyaml
PYTHONPATH=src .venv/bin/python -m pytest tests/ -q
PYTHONPATH=src .venv/bin/python examples/demo_run.py
```

## Paper
Karmendra Pandey, “Guarded Autonomy for Satellites: A Policy-Gated AI Agent
Framework for Safe Onboard Fault Response.” Preprint: Zenodo, DOI
[10.5281/zenodo.23425891](https://zenodo.org/records/23425891).
Peer-review target: *Journal of Space Operations & Communicator*.
Positioning: Simplex-inspired runtime assurance, translated from flight
control to LLM fault response — see `./similar-work-and-differentiation.md`.
