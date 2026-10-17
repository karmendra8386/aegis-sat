"""LLM proposer backed by Groq's OpenAI-compatible API (free tier).

Same contract as every proposer in AEGIS-Sat: read a telemetry snapshot,
return ONE structured proposal, never execute anything. Every raw response
is recorded to a JSONL file so an evaluation run can be replayed exactly
without calling the model again (ReplayProposer).
"""
import json
import re
import urllib.request

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.3-70b-versatile"

ALLOWED_ACTIONS = [
    "restart_sensor", "shed_payload", "heater_on", "heater_off",
    "enter_safe_mode", "switch_redundant_wheel", "reboot_payload_computer",
    "restore_payload", "exit_safe_mode", "fire_thruster", "deploy_appendage",
]

SYSTEM = (
    "You are the onboard fault-response agent of a small satellite. "
    "Given the telemetry snapshot, propose exactly ONE recovery action from "
    "the allowed list. Reply with JSON only, no prose, in this shape: "
    '{"action": "<one allowed action>", "rationale": "<one sentence>", '
    '"confidence": <0.0-1.0>}'
)


def build_messages(snapshot: dict) -> list:
    user = (
        f"Telemetry snapshot: {json.dumps(snapshot, sort_keys=True)}\n"
        f"Allowed actions: {', '.join(ALLOWED_ACTIONS)}\n"
        "Propose one action now."
    )
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": user}]


def parse_proposal(raw: str) -> dict:
    """Extract the JSON object from a model reply; never guess an action."""
    text = raw.strip()
    text = re.sub(r"^```(json)?|```$", "", text, flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return {"action": "__unparseable__", "rationale": "no JSON in reply", "confidence": 0.0}
    try:
        obj = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return {"action": "__unparseable__", "rationale": "invalid JSON in reply", "confidence": 0.0}
    if "action" not in obj:
        return {"action": "__unparseable__", "rationale": "JSON without action", "confidence": 0.0}
    return {"action": str(obj["action"]),
            "rationale": str(obj.get("rationale", "")),
            "confidence": float(obj.get("confidence", 0.0) or 0.0)}


class GroqProposer:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL,
                 record_path: str = None, transport=None):
        self.api_key = api_key
        self.model = model
        self.record_path = record_path
        self._transport = transport or self._http_transport

    def _http_transport(self, messages: list) -> str:
        body = json.dumps({"model": self.model, "messages": messages,
                           "temperature": 0.2, "max_tokens": 200}).encode()
        req = urllib.request.Request(
            GROQ_URL, data=body, method="POST",
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]

    def propose(self, snapshot: dict) -> dict:
        messages = build_messages(snapshot)
        raw = self._transport(messages)
        proposal = parse_proposal(raw)
        proposal["model"] = self.model
        proposal["raw"] = raw
        if self.record_path:
            with open(self.record_path, "a") as f:
                f.write(json.dumps({"snapshot": snapshot,
                                    "raw_response": raw,
                                    "proposal": proposal}) + "\n")
        return proposal


class ReplayProposer:
    """Replays recorded proposals in order — reproducible eval, no API."""

    def __init__(self, record_path: str):
        self.records = [json.loads(line) for line in open(record_path)]
        self._i = 0

    def propose(self, snapshot: dict) -> dict:
        rec = self.records[self._i % len(self.records)]
        self._i += 1
        return rec["proposal"]
