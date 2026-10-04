"""Auswertung: kleine Studien, Aufbau der Berichte, Vollständigkeit der vorgerechneten Datei."""

import pytest

import oa_constants as C
import oa_evaluation as E
import oa_formulas as F


def test_true_wait_matches_the_formula_by_hand():
    """ρ = 90 %, mittlere Abfertigung 3 min: λ = 0.3, μ = 1/3 -> Wq = 0.9/(1/3 − 0.3) = 27 min; ρ = 50 %: 3 min."""
    assert E.true_wait(90) == pytest.approx(27.0) and E.true_wait(50) == pytest.approx(3.0)
    with pytest.raises(ValueError):
        F.mean_wait(0.34, 1 / 3)


def test_replication_means_count_length_and_independence():
    means = E.replication_means(80, 2000, seed=3)
    assert len(means) == C.N_REPLICATIONS and len(set(means)) == C.N_REPLICATIONS
    assert E.replication_means(80, 2000, seed=3) == means                       # reproduzierbar
    deleted = E.replication_means(80, 2000, seed=3, delete_fraction=0.5)
    assert deleted != means                                                      # Löschen wirkt


def test_single_run_report_has_three_intervals_and_the_true_value():
    rep = E.single_run_report(90, 5000, 35, 20, 0)
    assert [r["key"] for r in rep["rows"]] == ["naive", "batch", "repl"]
    assert rep["truth"] == pytest.approx(27.0) and len(rep["waits"]) == 5000 and len(rep["acf"]) == C.ACF_LAGS
    for r in rep["rows"]:
        assert r["half"] > 0 and isinstance(r["covers"], bool)
        assert r["covers"] == (abs(r["mean"] - rep["truth"]) <= r["half"])
    naive, batch = rep["rows"][0], rep["rows"][1]
    assert naive["half"] < batch["half"]                                         # naiv ist viel schmaler


def test_single_run_report_warmup_changes_the_intervals_but_not_the_run():
    base = E.single_run_report(90, 5000, 35, 20, 0)
    cut = E.single_run_report(90, 5000, 35, 20, 30)
    assert base["waits"] == cut["waits"] and base["rows"][1]["mean"] != cut["rows"][1]["mean"]


def test_welch_report_has_the_expected_length_and_starts_below_the_level():
    curve = E.welch_report(90, 5)
    assert len(curve) == C.WELCH_N and curve[0] < E.true_wait(90) / 2             # leerer Start: anfangs kaum Wartezeit


def test_crn_paths_common_numbers_are_pathwise_ordered_independent_are_not():
    a, b_crn, b_ind = E.crn_paths(90, 10, 7, n=500)
    assert len(a) == len(b_crn) == len(b_ind) == 500
    assert all(y <= x + 1e-9 for x, y in zip(a, b_crn)) and any(y > x for x, y in zip(a, b_ind))


def test_coverage_study_small_cell_structure_and_ordering():
    cell = E.coverage_study(90, 1000, 60, seed_base=11)
    v = cell["variants"]
    expected = {"naive", "naive_stat", "batch5", "batch10", "batch20", "batch30", "del10", "del20", "del50", "mser",
                "stat", "repl10", "repl10_del20", "none"}
    assert set(v) == expected and cell["truth"] == pytest.approx(27.0) and cell["reps"] == 60
    for entry in v.values():
        assert 0.0 <= entry["cover"] <= 1.0 and entry["rel_half"] > 0 and entry["rel_std"] > 0
    assert v["none"] == v["batch20"]
    assert v["naive"]["cover"] < v["batch5"]["cover"] - 0.3                       # naiv trifft viel seltener
    assert v["naive"]["rel_half"] < v["batch20"]["rel_half"]


def test_each_strategy_actually_differs_from_doing_nothing():
    """Zweig-Test (Playbook): keine Strategie-Spalte darf mit 'nichts löschen' identisch sein, sonst läuft sie nie."""
    v = E.coverage_study(90, 2000, 30, seed_base=5)["variants"]
    for key in ("del10", "del20", "del50", "mser", "stat"):
        assert v[key]["bias_pct"] != v["none"]["bias_pct"], key


def test_crn_study_small_cell():
    out = E.crn_study(50, 10, 3000, 40, seed_base=3)
    assert out["truth_diff"] == pytest.approx(3.0 - 0.4545454545 / (0.3666666667 - 0.1666666667), rel=1e-6)
    assert out["variance_factor"] > 2 and out["sd_crn"] < out["sd_ind"]


def test_nearest_grid_rho_ties_go_to_the_smaller_value():
    assert E.nearest_grid_rho(60) == 50 and E.nearest_grid_rho(61) == 70 and E.nearest_grid_rho(97) == 95
    assert E.nearest_grid_rho(10) == 50


def test_precomputed_file_is_complete():
    pre = E.load_precomputed()
    assert {(c["rho_pct"], c["n"]) for c in pre["coverage"]} == {(r, n) for r in C.GRID_RHO_PCT for n in C.GRID_N}
    assert all(c["reps"] == pre["grid_reps"] == C.GRID_REPS for c in pre["coverage"])
    assert {(c["rho_pct"], c["speedup_pct"]) for c in pre["crn"]} == {(r, s) for r in C.GRID_RHO_PCT for s in C.CRN_SPEEDUPS}
    assert pre["crn_n"] == C.CRN_N and all(c["reps"] == C.CRN_REPS for c in pre["crn"])
    for c in pre["coverage"]:
        for method in C.METHOD_ORDER + ("none", "del10", "del20", "del50", "mser", "stat", "naive_stat", "repl10_del20"):
            assert method in c["variants"], (c["rho_pct"], c["n"], method)


def test_warmup_summary_counts_by_hand_on_a_fake_table():
    def cell(none, mser, del20, stat, naive=0.4, naive_stat=0.45):
        mk = lambda c: {"cover": c}
        return {"variants": {"none": mk(none), "mser": mk(mser), "del20": mk(del20), "stat": mk(stat),
                             "naive": mk(naive), "naive_stat": mk(naive_stat)}}
    fake = {"coverage": [cell(0.9, 0.8, 0.9, 0.95), cell(0.9, 0.91, 0.84, 0.9), cell(0.5, 0.5, 0.5, 0.5, naive=0.1)]}
    s = E.warmup_summary(fake)
    assert s == {"total": 3, "mser_worse": 1, "mser_better": 0, "del20_changed": 1, "stat_worse": 0, "stat_better": 1,
                 "naive_max": 0.4, "naive_stat_max": 0.45}
