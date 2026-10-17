"""Tamper-evident audit ledger: hash-chained records of every proposal,
gate decision, and state snapshot."""
import hashlib
import json
import time


class Ledger:
    def __init__(self):
        self.records = []
        self._prev = "GENESIS"

    def append(self, kind: str, payload: dict) -> dict:
        rec = {
            "ts": time.time(),
            "kind": kind,
            "payload": payload,
            "prev": self._prev,
        }
        rec["hash"] = hashlib.sha256(
            json.dumps(rec, sort_keys=True).encode()).hexdigest()[:16]
        self._prev = rec["hash"]
        self.records.append(rec)
        return rec

    def verify(self) -> bool:
        prev = "GENESIS"
        for rec in self.records:
            if rec["prev"] != prev:
                return False
            body = {k: rec[k] for k in ("ts", "kind", "payload", "prev")}
            if hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16] != rec["hash"]:
                return False
            prev = rec["hash"]
        return True
