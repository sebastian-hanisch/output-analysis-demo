"""Presets: Vollständigkeit, gültige Werte, Permalink-Konstanten."""

import pytest

import oa_constants as C
import oa_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP) == set(C.PRESET_ORDER) and len(C.PRESETS) == 4
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS) and C.PRESET_HELP[name]


def test_preset_values_are_valid_and_match_the_setting_specs():
    for preset in C.PRESETS.values():
        assert C.RHO_PCT_MIN <= preset["rho_pct"] <= C.RHO_PCT_MAX
        assert preset["n"] in C.N_OPTIONS and preset["batches"] in C.BATCH_OPTIONS
        assert C.WARMUP_PCT_MIN <= preset["warmup_pct"] <= C.WARMUP_PCT_MAX
        for key, state_key in P.PRESET_KEYS.items():
            P.SETTING_SPECS[state_key].caster(preset[key])


def test_preset_names_state_the_values_they_set():
    for name, preset in C.PRESETS.items():
        if "ρ" in name:
            assert f"{preset['rho_pct']} %" in name
    assert C.PRESETS["Kurzer Lauf (1 000 Lkw)"]["n"] == 1000


def test_default_preset_equals_the_default_settings():
    p = C.PRESETS["Normalfall (ρ = 90 %)"]
    assert (p["rho_pct"], p["n"], p["batches"], p["warmup_pct"], p["seed"]) == (
        C.DEFAULT_RHO_PCT, C.DEFAULT_N, C.DEFAULT_BATCHES, C.DEFAULT_WARMUP_PCT, C.DEFAULT_SEED)


def test_bounds_and_url_params():
    assert P.bounds("rho_slider") == (C.RHO_PCT_MIN, C.RHO_PCT_MAX) and P.bounds("seed_input") == (0, C.SEED_MAX)
    assert len({spec.url_param for spec in P.SETTING_SPECS.values()}) == len(P.SETTING_SPECS)


@pytest.mark.parametrize("value,expected", [(1000, 1000), (1400, 1000), (3000, 2000), (3600, 5000), (3500, 2000),
                                            (10**6, 50000), (1, 1000)])
def test_n_snaps_to_the_nearest_option(value, expected):
    assert P.snap_to_option("n_select", value) == expected


@pytest.mark.parametrize("value,expected", [(5, 5), (6, 5), (8, 10), (7, 5), (30, 30)])
def test_batches_snap_to_the_nearest_option(value, expected):
    assert P.snap_to_option("batches_select", value) == expected


@pytest.mark.parametrize("value,expected", [(0, 0), (3, 5), (12, 10), (13, 15), (50, 50)])
def test_warmup_snaps_to_the_step(value, expected):
    assert P.snap_to_step("warmup_slider", value) == expected


def test_fmt_int_uses_dots_as_thousands_separator_and_fmt_pct_a_space():
    assert C.fmt_int(10000) == "10.000" and C.fmt_int(950) == "950"
    assert C.fmt_pct(0.86) == "86 %" and C.fmt_pct(0.5) == "50 %" and C.fmt_pct(0.0) == "0 %"


def test_constants_are_consistent():
    assert set(C.METHOD_ORDER) == set(C.METHOD_LABELS) and set(C.WARMUP_ORDER) == set(C.WARMUP_LABELS)
    assert C.N_REPLICATIONS == 10 and C.GRID_N == C.N_OPTIONS and C.RHO_PCT_MAX < 100
    assert all(b <= 30 for b in C.BATCH_OPTIONS)            # t-Tabelle reicht bis 30 Freiheitsgrade genau
