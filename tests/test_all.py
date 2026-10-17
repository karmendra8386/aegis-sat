import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from aegis_sat import CubeSat, PolicyGate, Ledger, MockAgent

POL = os.path.join(os.path.dirname(__file__), "..", "policies", "fault_response.yaml")


def gate():
    return PolicyGate(POL)


def test_auto_action_executes():
    d = gate().evaluate({"action": "shed_payload"}, CubeSat())
    assert d.tier == "AUTO" and d.executed


def test_unknown_action_denied():
    d = gate().evaluate({"action": "open_everything"}, CubeSat())
    assert d.tier == "DENY" and not d.executed


def test_ground_only_action_denied():
    d = gate().evaluate({"action": "deploy_appendage"}, CubeSat())
    assert d.tier == "DENY" and not d.executed


def test_battery_floor_denies_costly_action():
    sat = CubeSat(soc=0.22)
    d = gate().evaluate({"action": "fire_thruster"}, sat)  # cost .05 -> .17 < floor .20
    assert d.tier == "DENY"


def test_blackout_holds_irreversible_escalation():
    sat = CubeSat(blackout=True)
    d = gate().evaluate({"action": "fire_thruster"}, sat)
    assert d.tier == "HOLD" and not d.executed


def test_eclipse_tightens_envelope():
    sat = CubeSat(eclipse=True, soc=0.40)
    d = gate().evaluate({"action": "heater_on"}, sat)  # AUTO normally; eclipse floor .30, margin < .15, cost > 0
    assert d.tier == "ESCALATE"


def test_ledger_chain_verifies_and_detects_tamper():
    led = Ledger()
    led.append("proposal", {"action": "shed_payload"})
    led.append("decision", {"tier": "AUTO"})
    assert led.verify()
    led.records[0]["payload"]["action"] = "fire_thruster"
    assert not led.verify()


def test_sim_dies_without_power_and_survives_shedding():
    sat = CubeSat(soc=0.10, eclipse=True)
    for _ in range(30):
        sat.step()
    assert sat.dead
    sat2 = CubeSat(soc=0.10, eclipse=True)
    sat2.apply("shed_payload")
    sat2.apply("enter_safe_mode")
    sat2.eclipse = False
    for _ in range(30):
        sat2.step()
    assert not sat2.dead and sat2.soc > 0.10


def test_below_floor_survival_actions_still_allowed():
    # Regression (Week-2 harness): already below the eclipse floor, the gate
    # must not deny zero-cost survival actions like shedding or safe mode.
    sat = CubeSat(soc=0.28, eclipse=True)  # eclipse floor is 0.30
    assert gate().evaluate({"action": "shed_payload"}, sat).executed
    assert gate().evaluate({"action": "enter_safe_mode"}, sat).executed
    # and a costly irreversible action still never executes autonomously
    assert not gate().evaluate({"action": "fire_thruster"}, sat).executed


def test_wheel_switch_auto_log_below_40_percent():
    # Item 6, Option B (decided 2026-10-11): dying wheel -> act now, log it
    sat = CubeSat(wheel_health=0.35)
    d = gate().evaluate({"action": "switch_redundant_wheel"}, sat)
    assert d.tier == "AUTO_LOG" and d.executed


def test_wheel_switch_escalates_when_wheel_healthy():
    sat = CubeSat(wheel_health=0.85)
    d = gate().evaluate({"action": "switch_redundant_wheel"}, sat)
    assert d.tier == "ESCALATE" and not d.executed


def test_mock_agent_bad_proposals_are_caught():
    g, agent = gate(), MockAgent()
    sat = CubeSat(blackout=True)
    for scen in ("blackout_fault", "payload_computer_crash"):
        d = g.evaluate(agent.propose(scen, sat), sat)
        assert not d.executed, f"{scen} should not execute, got {d}"
