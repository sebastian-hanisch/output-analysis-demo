"""SETTING_SPECS-Permalink-Muster, Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio).
Alle Regler sind immer sichtbar - es gibt keinen ausblendbaren Regler (also auch kein KEPT-Muster)."""

import random
from dataclasses import dataclass
from typing import Callable, Optional

import streamlit as st

import oa_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: Callable
    default: object
    lo: Optional[float] = None
    hi: Optional[float] = None


SETTING_SPECS = {
    "rho_slider": SettingSpec("rho", int, C.DEFAULT_RHO_PCT, C.RHO_PCT_MIN, C.RHO_PCT_MAX),
    "n_select": SettingSpec("n", int, C.DEFAULT_N, C.N_OPTIONS[0], C.N_OPTIONS[-1]),
    "batches_select": SettingSpec("b", int, C.DEFAULT_BATCHES, C.BATCH_OPTIONS[0], C.BATCH_OPTIONS[-1]),
    "warmup_slider": SettingSpec("w", int, C.DEFAULT_WARMUP_PCT, C.WARMUP_PCT_MIN, C.WARMUP_PCT_MAX),
    "seed_input": SettingSpec("seed", int, C.DEFAULT_SEED, 0, C.SEED_MAX),
}
PRESET_KEYS = {"rho_pct": "rho_slider", "n": "n_select", "batches": "batches_select", "warmup_pct": "warmup_slider",
               "seed": "seed_input"}
OPTIONS = {"n_select": C.N_OPTIONS, "batches_select": C.BATCH_OPTIONS}      # Regler, die nur feste Stufen kennen
STEPS = {"warmup_slider": C.WARMUP_PCT_STEP}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def snap_to_option(state_key, value):
    """Regler mit festen Stufen: ein Permalink-Wert dazwischen rastet auf die nächste Stufe ein (bei Gleichstand auf
    die kleinere)."""
    return min(OPTIONS[state_key], key=lambda o: (abs(o - value), o))


def snap_to_step(state_key, value):
    """Stufenregler mit Mindestwert: Permalink-Wert auf das nächste Vielfache der Schrittweite einrasten."""
    lo = SETTING_SPECS[state_key].lo
    step = STEPS[state_key]
    return int(lo + round((value - lo) / step) * step)


def load_permalink_settings():
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
                if spec.lo is not None:
                    value = max(spec.lo, value)
                if spec.hi is not None:
                    value = min(spec.hi, value)
                if state_key in OPTIONS:
                    value = snap_to_option(state_key, value)
                if state_key in STEPS:
                    value = min(spec.hi, snap_to_step(state_key, value))
                st.session_state[state_key] = value
            except (ValueError, TypeError):
                pass
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        st.session_state[state_key] = C.PRESETS[name][key]


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)
