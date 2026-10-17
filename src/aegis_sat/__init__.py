"""AEGIS-Sat: policy-gated agent framework for safe onboard fault response."""
from .sim import CubeSat
from .guard import PolicyGate, Decision
from .ledger import Ledger
from .agent import MockAgent

__all__ = ["CubeSat", "PolicyGate", "Decision", "Ledger", "MockAgent"]
__version__ = "0.0.1"
