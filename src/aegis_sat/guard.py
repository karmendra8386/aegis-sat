"""The policy gate — the core of AEGIS-Sat.

The agent proposes; the gate disposes. Evaluation order:
  1. Unknown action                       -> DENY
  2. Hard invariants (predicted state)    -> DENY if breached
  3. Policy base tier for the action
  4. Context-adaptive envelope:
       - blackout: ESCALATE cannot reach the ground, so non-reversible
         actions become HOLD (deny + safe mode), reversible ones stay
       - eclipse: battery floor rises, low-margin AUTO actions are
         downgraded to ESCALATE
  5. Irreversible actions are never below ESCALATE
The gate is deterministic and has no ML in it. That is the point.
"""
from dataclasses import dataclass
import copy
import yaml

TIER_ORDER = {"AUTO": 0, "AUTO_LOG": 1, "ESCALATE": 2, "DENY": 3}


@dataclass
class Decision:
    tier: str            # AUTO | AUTO_LOG | ESCALATE | DENY | HOLD
    action: str
    reason: str
    executed: bool


class PolicyGate:
    def __init__(self, policy_path: str):
        with open(policy_path) as f:
            self.policy = yaml.safe_load(f)
        self.inv = self.policy["invariants"]
        self.actions = self.policy["actions"]

    def _floor(self, sat) -> float:
        return self.inv["eclipse_battery_floor_soc"] if sat.eclipse else self.inv["battery_floor_soc"]

    def evaluate(self, proposal: dict, sat) -> Decision:
        action = proposal.get("action", "")
        if action not in self.actions:
            return Decision("DENY", action, "unknown action", False)
        spec = self.actions[action]
        cost = float(spec.get("energy_cost_soc", 0.0))

        # Hard invariants. The floor stops an action from *pushing* the
        # spacecraft across it — it must never block zero-cost survival
        # actions when the state is already below the floor (Week-2 harness
        # caught exactly that: safe mode itself was being denied in eclipse).
        if cost > 0:
            if sat.soc - cost < 0.05:
                return Decision("DENY", action,
                                f"predicted SoC {sat.soc - cost:.2f} breaches survival floor 0.05",
                                False)
            if sat.soc >= self._floor(sat) and sat.soc - cost < self._floor(sat):
                return Decision("DENY", action,
                                f"predicted SoC {sat.soc - cost:.2f} breaches floor {self._floor(sat):.2f}",
                                False)
        if sat.temp_c > self.inv["max_temp_c"] and action not in ("heater_off", "enter_safe_mode", "shed_payload"):
            return Decision("DENY", action, "thermal invariant already breached; cooling actions only", False)

        tier = spec["tier"]

        # operator-set conditional exception (adaptive envelope): e.g. the
        # redundant-wheel switch is AUTO_LOG when wheel health is dying,
        # ESCALATE otherwise. Checked before the irreversibility floor.
        cond = spec.get("auto_log_if") or {}
        if "wheel_health_below" in cond and sat.wheel_health < float(cond["wheel_health_below"]):
            tier = "AUTO_LOG"
            executed = True
            return Decision(tier, action,
                            f"conditional AUTO_LOG: wheel health {sat.wheel_health:.2f} < {cond['wheel_health_below']}",
                            executed)

        # irreversible actions never go below ESCALATE
        if not spec.get("reversible", True) and TIER_ORDER[tier] < TIER_ORDER["ESCALATE"]:
            tier = "ESCALATE"

        # context-adaptive envelope: eclipse tightens low-margin autonomy
        if sat.eclipse and tier == "AUTO" and sat.soc < self._floor(sat) + 0.15 and cost > 0:
            tier = "ESCALATE"

        # context-adaptive envelope: blackout changes what ESCALATE means
        if sat.blackout and tier == "ESCALATE":
            if spec.get("reversible", True):
                return Decision("ESCALATE", action,
                                "blackout: reversible, but held for ground at next contact", False)
            return Decision("HOLD", action,
                            "blackout + irreversible: hold spacecraft safe, no ground to ask", False)

        executed = tier in ("AUTO", "AUTO_LOG")
        reason = f"base tier {spec['tier']}" + ("" if tier == spec["tier"] else f", adjusted to {tier} by envelope/invariants")
        return Decision(tier, action, reason, executed)
