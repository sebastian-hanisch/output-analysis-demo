"""AppTest-Rauchtests: Voreinstellung, jedes Preset, Randwerte, Würfel-Knopf, Permalink-Grenzen, Abschnitte, Footer."""

import random
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import oa_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(**state):
    at = AppTest.from_file(APP, default_timeout=300)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]


def _metric(at, prefix):
    return next(m for m in at.metric if m.label.startswith(prefix))


def test_default_run_has_no_exception_and_shows_three_intervals():
    at = _run()
    _ok(at)
    labels = [m.label for m in at.metric]
    assert any(l.startswith("naiv") for l in labels) and any(l.startswith("Batch Means") for l in labels)
    assert any("unabhängige Wiederholungen" in l for l in labels)
    assert any("Ein einzelner Lauf sagt nur" in i.value for i in at.info)


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_button_runs(name):
    at = _run()
    next(b for b in at.button if b.key == f"preset_{name}").click().run()
    _ok(at)
    p = C.PRESETS[name]
    assert at.session_state["rho_slider"] == p["rho_pct"] and at.session_state["n_select"] == p["n"]
    assert at.metric


@pytest.mark.parametrize("kw", [dict(rho_slider=C.RHO_PCT_MIN), dict(rho_slider=C.RHO_PCT_MAX),
                                 dict(n_select=C.N_OPTIONS[0]), dict(n_select=C.N_OPTIONS[-1]),
                                 dict(batches_select=C.BATCH_OPTIONS[0]), dict(batches_select=C.BATCH_OPTIONS[-1]),
                                 dict(warmup_slider=C.WARMUP_PCT_MAX), dict(n_select=1000, warmup_slider=50, rho_slider=97),
                                 dict(cov_n_select=50000), dict(crn_speedup=50)])
def test_extreme_settings_run(kw):
    _ok(_run(**kw))


def test_dice_button_changes_the_seed_and_the_result(monkeypatch):
    """Der Würfel zieht sonst einen unseeded Zufalls-Seed; bei gerundeten Kennzahlen kollidiert ein Zufallsseed manchmal mit dem
    Standard-Seed (gemessen: 40 Würfe, bis zu 9 gleiche Anzeigen), deshalb ist der gewürfelte Seed im Test fest."""
    monkeypatch.setattr(random, "randint", lambda a, b: 508145)
    at = _run()
    old_seed, old = at.session_state["seed_input"], _metric(at, "naiv").value
    next(b for b in at.button if b.label == "🎲 Neuen Lauf würfeln").click().run()
    _ok(at)
    assert at.session_state["seed_input"] == 508145            # der feste Seed ist wirklich verwendet worden
    assert at.session_state["seed_input"] != old_seed and _metric(at, "naiv").value != old


def test_warmup_slider_changes_the_main_intervals():
    base = _run()
    cut = _run(warmup_slider=30)
    _ok(cut)
    assert _metric(base, "Batch Means").value != _metric(cut, "Batch Means").value


def test_batches_select_changes_the_label_and_the_interval():
    at = _run(batches_select=5)
    _ok(at)
    assert _metric(at, "Batch Means").label == "Batch Means, 5 Batches"


def test_permalink_values_are_clamped_and_snapped():
    at = AppTest.from_file(APP, default_timeout=300)
    at.query_params["rho"] = "9999"
    at.query_params["n"] = "3000"
    at.query_params["b"] = "7"
    at.query_params["w"] = "13"
    at.run()
    _ok(at)
    assert at.session_state["rho_slider"] == C.RHO_PCT_MAX and at.session_state["n_select"] == 2000
    assert at.session_state["batches_select"] == 5 and at.session_state["warmup_slider"] == 15


def test_permalink_ignores_garbage():
    at = AppTest.from_file(APP, default_timeout=300)
    at.query_params["rho"] = "viel"
    at.query_params["seed"] = "x"
    at.run()
    _ok(at)
    assert at.session_state["rho_slider"] == C.DEFAULT_RHO_PCT and at.session_state["seed_input"] == C.DEFAULT_SEED


def test_charts_sections_and_limits_table_are_present():
    at = _run()
    _ok(at)
    assert len(at.get("plotly_chart")) == 7
    headers = [s.value for s in at.subheader]
    assert any("Abdeckung" in h for h in headers) and any("Warm-up" in h for h in headers)
    assert any("Gemeinsame Zufallszahlen" in h for h in headers) and any("Wo die Annahmen enden" in h for h in headers)
    table = next(m.value for m in at.markdown if "Wer setzt an" in m.value)
    for name in ("Zeitvariable Ankünfte", "Splitting", "Kingman", "Jackson-Netze"):
        assert name in table
    assert "geplant" not in table      # die Linie wird erst vollständig veröffentlicht, kein Status-Zusatz


def test_seed_control_uses_the_portfolio_wording():
    at = _run()
    assert [n.label for n in at.number_input] == ["Zufalls-Seed"]


def test_related_demos_are_linked_and_footer_is_present():
    at = _run()
    text = " ".join(c.value for c in at.caption)
    assert "mm1-queue-demo" in text and "forecast-interval-demo" in text
    assert "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net)" in text
