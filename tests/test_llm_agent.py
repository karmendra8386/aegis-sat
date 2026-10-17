import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from aegis_sat.llm_agent import GroqProposer, ReplayProposer, parse_proposal
from aegis_sat import CubeSat, PolicyGate

POL = os.path.join(os.path.dirname(__file__), "..", "policies", "fault_response.yaml")


def fake_transport(reply):
    return lambda messages: reply


def test_parse_plain_json():
    p = parse_proposal('{"action": "shed_payload", "rationale": "low battery", "confidence": 0.9}')
    assert p["action"] == "shed_payload" and p["confidence"] == 0.9


def test_parse_fenced_json():
    p = parse_proposal('```json\n{"action": "heater_off", "rationale": "hot", "confidence": 0.5}\n```')
    assert p["action"] == "heater_off"


def test_parse_garbage_is_unparseable_not_guessed():
    p = parse_proposal("I think you should probably do something about the battery.")
    assert p["action"] == "__unparseable__"


def test_unparseable_proposal_is_denied_by_gate():
    d = PolicyGate(POL).evaluate({"action": "__unparseable__"}, CubeSat())
    assert d.tier == "DENY" and not d.executed


def test_record_and_replay_roundtrip(tmp_path):
    rec = tmp_path / "runs.jsonl"
    prop = GroqProposer("test-key", record_path=str(rec),
                        transport=fake_transport('{"action": "fire_thruster", "rationale": "regain control", "confidence": 0.7}'))
    out = prop.propose({"soc": 0.3, "blackout": True})
    assert out["action"] == "fire_thruster"
    lines = open(rec).read().strip().splitlines()
    assert len(lines) == 1 and json.loads(lines[0])["raw_response"]
    replayed = ReplayProposer(str(rec)).propose({})
    assert replayed["action"] == "fire_thruster"


def test_llm_bad_proposal_still_blocked_in_blackout():
    prop = GroqProposer("test-key",
                        transport=fake_transport('{"action": "fire_thruster", "rationale": "regain control", "confidence": 0.7}'))
    sat = CubeSat(blackout=True)
    d = PolicyGate(POL).evaluate(prop.propose(sat.snapshot()), sat)
    assert d.tier == "HOLD" and not d.executed
