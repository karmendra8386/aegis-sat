import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from aegis_sat import CubeSat
from aegis_sat.eval import ground_approves, run_all

POL = os.path.join(os.path.dirname(__file__), "..", "policies", "fault_response.yaml")


def test_ground_never_approves_hard_invariant_breach():
    sat = CubeSat()
    assert ground_approves("deploy_appendage", sat) is False
    sat.blackout = True
    assert ground_approves("fire_thruster", sat) is False


def test_ground_approves_symptom_fitting_wheel_switch():
    sat = CubeSat(); sat.wheel_health = 0.50
    assert ground_approves("switch_redundant_wheel", sat) is True
    sat.wheel_health = 0.95
    assert ground_approves("switch_redundant_wheel", sat) is False


def test_delayed_replies_resolve_and_guarded_stays_safe():
    eps = run_all(POL, n=100)
    guarded = [e for e in eps if e.setup == "guarded"]
    unguarded = [e for e in eps if e.setup == "unguarded"]
    # the headline invariant: the guarded setup never executes an unsafe action
    assert sum(e.unsafe_executed for e in guarded) == 0
    # sanity: the unguarded agent really does execute unsafe actions
    assert sum(e.unsafe_executed for e in unguarded) > 0
    # the delayed-reply model actually resolves escalations both ways
    assert sum(e.escalations_approved for e in guarded) > 0
    # escalations can now complete a wheel recovery that Week 2 could not
    wheel = [e for e in guarded if e.scenario == "wheel_degradation"]
    assert sum(e.outcome == "full_recovery" for e in wheel) > 0
