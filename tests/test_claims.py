"""JEDE Zahl aus README und App-Texten wird hier nachgerechnet: Formelwerte exakt, Messreihen-Zahlen aus der
vorgerechneten Datei (400 Läufe je Zelle, Standardfehler einer Abdeckung höchstens 2.5 Prozentpunkte), daher mit Marge
und nie auf einen einzelnen verrauschten Wert gepinnt."""

import pytest

import oa_constants as C
import oa_evaluation as E

PRE = E.load_precomputed()


def cov(rho, n, key="naive"):
    return E.coverage_cell(PRE, rho, n)["variants"][key]["cover"]


def var(rho, n):
    return E.coverage_cell(PRE, rho, n)["variants"]


def test_true_values_quoted_in_the_texts():
    assert E.true_wait(90) == pytest.approx(27.0) and E.true_wait(50) == pytest.approx(3.0)


def test_naive_interval_covers_far_below_95_percent_in_every_cell():
    """Das naive 95-%-Intervall trifft in KEINER der 30 Zellen häufiger als etwa jedes zweite Mal (auch nicht mit Start im
    Gleichgewicht) und wird mit längeren Läufen nicht besser."""
    ws = E.warmup_summary(PRE)
    assert ws["total"] == 30 and ws["naive_max"] < 0.56 and ws["naive_stat_max"] < 0.57
    for rho in C.GRID_RHO_PCT:
        assert abs(cov(rho, 1000) - cov(rho, 50000)) < 0.12


def test_naive_coverage_by_utilisation_at_10000_trucks():
    """README: 49 % (ρ 50), 28 % (70), 18 % (80), 9 % (90), 4 % (95)."""
    for rho, expected in ((50, 0.49), (70, 0.28), (80, 0.18), (90, 0.09), (95, 0.04)):
        assert cov(rho, 10000) == pytest.approx(expected, abs=0.06), rho
    assert cov(50, 10000) > cov(70, 10000) > cov(80, 10000) > cov(90, 10000) > cov(95, 10000) - 0.005


def test_batch_means_coverage_quoted_in_readme_and_preset_help():
    assert cov(90, 10000, "batch20") == pytest.approx(0.86, abs=0.06)           # Preset "Normalfall": 86 %
    assert cov(50, 10000, "batch20") == pytest.approx(0.93, abs=0.05)           # Preset "Entspannt": 93 %
    assert cov(95, 50000, "batch20") == pytest.approx(0.85, abs=0.06)           # Preset "Fast voll": 85 %
    assert cov(90, 1000, "batch20") == pytest.approx(0.55, abs=0.08)            # Preset "Kurzer Lauf": 55 %
    assert cov(90, 1000, "batch5") == pytest.approx(0.74, abs=0.08)             # ... und 74 % mit 5 Batches
    assert round(cov(90, 10000), 2) == pytest.approx(0.09, abs=0.06)            # Preset "Normalfall": naiv 9 %
    assert round(cov(50, 10000), 2) == pytest.approx(0.49, abs=0.06)            # Preset "Entspannt": naiv 49 %


def test_coverage_falls_with_the_number_of_batches_at_high_utilisation():
    """Abbildung/Tabelle: bei ρ = 95 sinkt die Abdeckung von 5 über 10 und 20 auf 30 Batches (für 5 000 bis 50 000 Lkw)."""
    for n in (5000, 10000, 20000, 50000):
        c = [cov(95, n, f"batch{b}") for b in C.BATCH_OPTIONS]
        assert c[0] > c[1] > c[2] > c[3] - 0.01, (n, c)


def test_naive_interval_is_too_narrow_by_the_factors_quoted():
    """README: Faktor etwa 3 (ρ 50), 18 (ρ 90), 36 (ρ 95) bei 10 000 Lkw: 1.96 · Streuung eines Laufs / mittlere Halbbreite."""
    def factor(rho):
        v = var(rho, 10000)["naive"]
        return 1.96 * v["rel_std"] / v["rel_half"]

    assert factor(50) == pytest.approx(3.1, rel=0.25)
    assert factor(90) == pytest.approx(18.3, rel=0.25)
    assert factor(95) == pytest.approx(35.9, rel=0.3)


def test_warmup_summary_counts_quoted_in_readme():
    """README: MSER-5 liegt in 23 von 30 Zellen mehr als 3 Punkte unter 'nichts löschen' und in keiner darüber; die ersten
    20 % löschen ändert die Abdeckung in keiner Zelle; Start im Gleichgewicht hilft in 4 Zellen und schadet nie."""
    ws = E.warmup_summary(PRE)
    assert ws["total"] == 30 and ws["mser_better"] == 0 and 17 <= ws["mser_worse"] <= 28
    assert ws["del20_changed"] == 0 and ws["stat_worse"] == 0 and 2 <= ws["stat_better"] <= 7


def test_mser_biases_the_mean_downwards_in_most_cells():
    cells = [c["variants"] for c in PRE["coverage"]]
    assert sum(1 for v in cells if v["mser"]["bias_pct"] < -1) >= 20
    v = var(90, 10000)
    assert v["mser"]["bias_pct"] < -4 and v["none"]["bias_pct"] > -3


def test_start_bias_at_short_high_utilisation_runs_and_the_fix_by_equilibrium_start():
    """README: ρ = 95 %, 1 000 Lkw: Mittelwert ohne Löschen etwa −32 %, mit Start im Gleichgewicht etwa +1 %; unabhängige
    Wiederholungen (10 × 100) liegen etwa −70 % daneben."""
    v = var(95, 1000)
    assert v["none"]["bias_pct"] == pytest.approx(-31.8, abs=8)
    assert abs(v["stat"]["bias_pct"]) < 8
    assert v["repl10"]["bias_pct"] == pytest.approx(-70, abs=8)


def test_common_random_numbers_quoted_in_readme():
    """README: Varianzfaktor 63 / 15 / 6 / 1.9 bei ρ = 50 % und 5 / 10 / 20 / 50 % schnellerer Abfertigung, bei ρ = 90 %:
    3.5 / 1.7 / 1.2 / 1.0; bei ρ = 95 %: 1.7 / 1.2 / 1.1 / 1.0. Die Differenz bleibt unverzerrt."""
    f = {(c["rho_pct"], c["speedup_pct"]): c for c in PRE["crn"]}
    assert f[(50, 5)]["variance_factor"] > f[(50, 10)]["variance_factor"] > f[(50, 20)]["variance_factor"] > f[(50, 50)]["variance_factor"]
    assert f[(50, 10)]["variance_factor"] == pytest.approx(15, rel=0.4)
    assert f[(90, 10)]["variance_factor"] == pytest.approx(1.7, rel=0.4)
    assert f[(95, 10)]["variance_factor"] == pytest.approx(1.2, abs=0.35)
    for rho in C.GRID_RHO_PCT:
        assert f[(rho, 50)]["variance_factor"] < f[(rho, 5)]["variance_factor"]
    for c in PRE["crn"]:
        se = c["sd_crn"] / PRE["crn_reps"] ** 0.5
        assert abs(c["mean_crn"] - c["truth_diff"]) < 5 * se + 1e-9, (c["rho_pct"], c["speedup_pct"])


def test_autocorrelation_of_neighbouring_waits_quoted_in_readme():
    """README: bei ρ = 90 % beträgt die Autokorrelation benachbarter Wartezeiten rund 0.99 (Standardlauf)."""
    rep = E.single_run_report(90, 10000, 35, 20, 0)
    assert rep["acf"][0] > 0.98
