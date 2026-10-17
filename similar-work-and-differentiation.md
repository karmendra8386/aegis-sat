# AEGIS-Sat — Similar Work and How Ours Is Different
**Checked 11 Oct 2026 — honest positioning note for Karmendra Pandey**

## Short answer
Yes, similar work exists — in five buckets. The idea of a safety gate in front of an
untrusted controller is about 30 years old. If our paper claimed we invented that,
reviewers would reject it on sight. Our contribution is narrower and defensible:
**we translate that proven idea from the flight-control level to the LLM-agent /
mission-operations level, and we publish the first open benchmark that measures it.**
*(“First” = to our knowledge, from this scan — to be re-verified before submission.)*

## The five buckets

### 1. Simplex / Runtime Assurance (RTA) — the ancestor
- **What it is:** A high-performance, unverified controller flies the vehicle while a
  simple verified safety controller watches; the moment safety is threatened, authority
  switches to the safe controller. Used for UAVs, aircraft, and spacecraft docking.
- **Same as ours:** the core pattern — never trust the smart component, always gate it.
- **Different:** RTA works on raw control signals (thrust, torque) with formal math.
  It does not reason about *faults*, does not handle natural-language agent proposals,
  has no “ask the ground” tier, and its rules are not readable by an operator.

### 2. Shielded learning / AMPLE-GNC — the closest academic cousin
- **What it is:** Recent spacecraft papers pair a capable learned guidance/control
  stack with a verified runtime “shield” that blocks or corrects unsafe commands,
  sometimes with statistical (conformal) safety certificates.
- **Same as ours:** a learned component plus a shield, evaluated in closed loop.
- **Different:** they shield RL/GNC controllers for attitude and proximity operations,
  and the shield is a formal model few operators can read or change. Ours guards an
  LLM agent doing *fault response* (battery, thermal, wheel, comms faults), the gate is
  plain YAML an operator can edit, and the output includes escalation and an audit trail.

### 3. Shield AI Hivemind + Sedaro SAFE — the closest flown, commercial system
- **What it is:** Reported in-orbit demonstrations where a physics digital twin
  simulates every proposed command before execution; only commands that clear the
  simulation run. Proprietary, defence-focused.
- **Same as ours:** every AI command is checked before it touches the spacecraft.
- **Different:** their gate is a heavy, high-fidelity physics simulation running on
  powerful onboard compute — a black box you must trust. Ours is a light, deterministic
  *policy* gate (state limits, reversibility, permission tiers) that runs anywhere,
  is fully open, and adds ground escalation + audit. The two are complementary:
  policy first (is this allowed?), simulation second (will this work?) — noted as
  future work in our paper, not claimed as ours.

### 4. Traditional FDIR, NASA OnAIR, AIKO — the incumbents
- **What it is:** FDIR is the standard onboard rulebook for known faults. NASA’s OnAIR
  is a research platform for onboard AI applications. AIKO’s products detect telemetry
  anomalies (GENE) and support autonomous operations (OLIVER) commercially.
- **Same as ours:** same problem — keep the spacecraft alive when things break.
- **Different:** FDIR only handles pre-foreseen faults and cannot use an LLM’s
  reasoning about a *new* fault. OnAIR is a platform, not a safety gate for agents.
  AIKO is closed and product-focused; none of them publish an open gate benchmark
  for LLM proposers with unsafe-action numbers.

### 5. LLM satellite operators + agent portfolio projects — the nearest neighbours
- **What it is:** MIT-led LLM spacecraft operators in simulation games; 2025 agent
  architectures for satellite operations; open GitHub multi-agent systems that mix
  LLM agents with a rule-based conflict resolver or lightweight human-in-the-loop
  guardrails (confidence checks, review for critical calls).
- **Same as ours:** LLM agents, some rule layer, satellite operations.
- **Different:** their rule layers are ad-hoc code inside one demo, not a published
  policy spec. None run the head-to-head experiment — rule-only vs. unguarded agent
  vs. guarded agent on the same injected faults — and none report the key safety
  metric: **unsafe actions that would have executed without the gate.** Several use
  simulated telemetry only; we anchor on real ESA OPS-SAT-AD and NASA SMAP/MSL data.

## Our differentiation — the five-part combination nobody publishes together
1. **Level:** gate sits at the fault-response / mission-operations level, in front of
   an LLM proposer — not at the raw control-signal level.
2. **Readable policy:** AUTO / AUTO+LOG / ESCALATE / DENY tiers in YAML an operator
   can read, change, and sign — no formal-methods expertise needed.
3. **The benchmark:** fault-injection evaluation, same 6 scenarios, 3 setups,
   headline metric = unsafe actions executed (plus recovery rate and time-to-safe).
4. **Audit ledger:** tamper-evident record of every proposal and gate decision —
   built for the trust question operators actually ask: “prove what the AI did.”
5. **Open + real data:** full code and policies public, anchored on ESA/NASA telemetry.

## One sharpening I recommend we add — our signature novelty
**Context-adaptive autonomy envelope:** the gate is not static. Its tiers tighten or
loosen with context — during a comms blackout the ESCALATE tier changes (there is no
ground to ask, so the gate holds the spacecraft safe and only allows reversible
actions), in eclipse the battery floor rises, and as power margin recovers, autonomy
widens again. Static shields do not do this; FDIR does not do this; the LLM demos
do not do this. This gives the paper one named, testable idea of its own, on top of
the benchmark.

## How we must position the paper (so it survives review)
- Say openly: “Simplex-inspired runtime assurance, translated to LLM fault response.”
- Never claim we invented gating, shields, or autonomous fault recovery.
- Claim only: the policy-tier design, the context-adaptive envelope, the open
  benchmark with unsafe-action metrics, and the audit ledger — together, in the open.
