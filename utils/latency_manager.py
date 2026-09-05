"""
latency_manager.py - Dynamic Inter-Agent Communication Latency & Timing Controller
Manages dispatch delay, text settling polling intervals, debate timeouts, and speed profiles.
"""

import os
import json

CONFIG_FILE = os.path.join("json", "latency_config.json")

DEFAULT_CONFIG = {
    "profile": "balanced",
    "dispatch_delay_sec": 1.5,
    "check_interval_sec": 1.5,
    "debate_delay_sec": 2.0,
    "max_timeout_sec": 120,
    "typing_simulation_ms": 50
}

PROFILES = {
    "turbo": {
        "profile": "turbo",
        "dispatch_delay_sec": 0.5,
        "check_interval_sec": 0.5,
        "debate_delay_sec": 0.8,
        "max_timeout_sec": 60,
        "typing_simulation_ms": 10
    },
    "balanced": {
        "profile": "balanced",
        "dispatch_delay_sec": 1.5,
        "check_interval_sec": 1.5,
        "debate_delay_sec": 2.0,
        "max_timeout_sec": 120,
        "typing_simulation_ms": 50
    },
    "paced": {
        "profile": "paced",
        "dispatch_delay_sec": 3.5,
        "check_interval_sec": 2.5,
        "debate_delay_sec": 4.0,
        "max_timeout_sec": 180,
        "typing_simulation_ms": 120
    }
}

def load_latency_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                res = DEFAULT_CONFIG.copy()
                res.update(data)
                return res
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_latency_config(cfg: dict):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

def set_latency_profile(profile_name: str) -> dict:
    if profile_name in PROFILES:
        cfg = PROFILES[profile_name]
        save_latency_config(cfg)
        return cfg
    return load_latency_config()
