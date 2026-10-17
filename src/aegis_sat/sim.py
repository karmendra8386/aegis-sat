"""Minimal CubeSat simulator: power, thermal, attitude, comms.

Deliberately small and deterministic. It models just enough physics for the
policy gate to reason about: state of charge, temperature, wheel health,
eclipse and comms-blackout windows, and spacecraft mode.
"""
from dataclasses import dataclass, field

MODES = ("NOMINAL", "SAFE", "PAYLOAD_ON")


@dataclass
class CubeSat:
    soc: float = 0.85            # battery state of charge, 0..1
    temp_c: float = 18.0         # internal temperature
    wheel_health: float = 1.0    # 1 = healthy, 0 = failed
    eclipse: bool = False
    blackout: bool = False       # no ground contact possible
    mode: str = "NOMINAL"
    heater_on: bool = False
    payload_on: bool = True
    dead: bool = False

    # power model (per step, abstract units)
    SOLAR_IN = 0.020
    BASE_LOAD = 0.008
    PAYLOAD_LOAD = 0.006
    HEATER_LOAD = 0.004

    def step(self, steps: int = 1) -> None:
        for _ in range(steps):
            if self.dead:
                return
            inflow = 0.0 if self.eclipse else self.SOLAR_IN
            load = self.BASE_LOAD
            if self.payload_on:
                load += self.PAYLOAD_LOAD
            if self.heater_on:
                load += self.HEATER_LOAD
            self.soc = min(1.0, max(0.0, self.soc + inflow - load))
            # thermal drift: heater warms, eclipse cools, sun warms slightly
            target = 20.0 + (14.0 if self.heater_on else 0.0) + (-8.0 if self.eclipse else 2.0)
            self.temp_c += 0.12 * (target - self.temp_c)
            if self.soc <= 0.02 or self.temp_c > 75.0:
                self.dead = True

    def snapshot(self) -> dict:
        return {
            "soc": round(self.soc, 3),
            "temp_c": round(self.temp_c, 1),
            "wheel_health": round(self.wheel_health, 2),
            "eclipse": self.eclipse,
            "blackout": self.blackout,
            "mode": self.mode,
            "dead": self.dead,
        }

    # -- physical actions (only the gate may authorise these) -------------
    def apply(self, action: str) -> None:
        if action == "shed_payload":
            self.payload_on = False
            if self.mode == "PAYLOAD_ON":
                self.mode = "NOMINAL"
        elif action == "restore_payload":
            self.payload_on = True
        elif action == "heater_on":
            self.heater_on = True
        elif action == "heater_off":
            self.heater_on = False
        elif action == "enter_safe_mode":
            self.mode = "SAFE"
            self.payload_on = False
        elif action == "exit_safe_mode":
            if self.mode == "SAFE":
                self.mode = "NOMINAL"
        elif action == "restart_sensor":
            pass  # no state change beyond clearing a stuck reading
        elif action == "switch_redundant_wheel":
            self.wheel_health = max(self.wheel_health, 0.9)
            self.soc = max(0.0, self.soc - 0.01)
        elif action == "reboot_payload_computer":
            self.soc = max(0.0, self.soc - 0.015)
        elif action == "fire_thruster":
            self.soc = max(0.0, self.soc - 0.05)
        elif action == "deploy_appendage":
            self.soc = max(0.0, self.soc - 0.03)
        else:
            raise ValueError(f"unknown action: {action}")
