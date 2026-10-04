"""Schätzer-Einheiten gegen Handrechnung (Mini-Reihen) und scipy als unabhängige Referenz für die t-Quantile."""

import math

import pytest

import oa_estimators as E


@pytest.mark.parametrize("df", list(range(1, 31)))
def test_t_quantile_matches_scipy_up_to_30_degrees_of_freedom(df):
    stats = pytest.importorskip("scipy.stats")
    assert E.t_quantile(df) == pytest.approx(stats.t.ppf(0.975, df), abs=6e-4)


@pytest.mark.parametrize("df", [31, 39, 40, 59, 60, 119, 120, 500, 10**6])
def test_t_quantile_above_30_is_slightly_conservative_never_too_small(df):
    stats = pytest.importorskip("scipy.stats")
    exact = stats.t.ppf(0.975, df)
    assert exact - 1e-3 <= E.t_quantile(df) <= exact + 0.03


def test_t_quantile_rejects_zero_degrees_of_freedom():
    with pytest.raises(ValueError):
        E.t_quantile(0)


def test_batch_means_by_hand_and_remainder_is_dropped():
    assert E.batch_means(list(range(1, 11)), 5) == pytest.approx([1.5, 3.5, 5.5, 7.5, 9.5])
    assert E.batch_means(list(range(1, 12)), 5) == pytest.approx([1.5, 3.5, 5.5, 7.5, 9.5])     # 11 -> Rest verworfen
    with pytest.raises(ValueError):
        E.batch_means([1, 2], 5)


def test_interval_by_hand():
    """Werte 1, 2, 3: Mittel 2, s = 1, Halbbreite t(2)·1/√3 = 4.303/√3."""
    mean, half = E.naive_interval([1, 2, 3])
    assert mean == pytest.approx(2.0) and half == pytest.approx(4.303 / math.sqrt(3))
    assert E.replication_interval([1, 2, 3]) == pytest.approx((mean, half))


def test_batch_interval_uses_the_batch_means_not_the_raw_values():
    x = [1, 3, 5, 7, 9, 11, 13, 15]                       # 4 Batches à 2: Mittel 2, 6, 10, 14; s = 5.164
    mean, half = E.batch_means_interval(x, 4)
    assert mean == pytest.approx(8.0) and half == pytest.approx(3.182 * 5.163978 / 2, rel=1e-4)


def test_naive_interval_is_much_narrower_than_batch_interval_on_a_strongly_autocorrelated_series():
    x = [math.sin(i / 40.0) for i in range(2000)]         # langsame Schwingung: Nachbarwerte fast gleich
    assert E.naive_interval(x)[1] < 0.5 * E.batch_means_interval(x, 10)[1]


def test_delete_initial():
    assert E.delete_initial(list(range(10)), 0.3) == [3, 4, 5, 6, 7, 8, 9]
    assert E.delete_initial([1, 2, 3], 0) == [1, 2, 3]
    for bad in (-0.1, 1.0):
        with pytest.raises(ValueError):
            E.delete_initial([1, 2, 3], bad)


def test_mser_cuts_at_the_end_of_an_obvious_transient():
    """Erst 20 Werte fallend von 10 auf 1.45, danach konstant 1: Blöcke 0-3 gehören zum Einschwingen, ab Block 4 ist die
    Summe der Abweichungsquadrate 0 -> kleinster Abschneidepunkt mit Statistik 0 ist d = 4 Blöcke = 20 Werte."""
    x = [10 - 0.45 * i for i in range(20)] + [1.0] * 80
    assert E.mser_truncation(x) == 20


def test_mser_cuts_nothing_on_a_constant_series():
    assert E.mser_truncation([2.0] * 100) == 0


def test_mser_respects_the_maximum_fraction_and_the_block_size():
    x = [100 - i for i in range(100)]                      # nie stationär: wählt höchstens die Hälfte
    cut = E.mser_truncation(x, block=5, max_fraction=0.5)
    assert cut % 5 == 0 and cut <= 50


def test_mser_statistic_by_hand_on_three_blocks():
    """Blockmittel y = [3, 1, 1] (Block 1): d = 0: Σ(y−ȳ)²/m² = (4/9·... ) -> (3−5/3)²+2·(1−5/3)² = 16/9+8/9 = 24/9, /9 = 0.296;
    d = 1: ȳ = 1, Σ = 0 -> kleiner, also wird 1 Block = `block` Werte verworfen (max_fraction 0.5·3 -> d ≤ 1)."""
    assert E.mser_truncation([3, 3, 1, 1, 1, 1], block=2, max_fraction=0.5) == 2


def test_welch_curve_by_hand():
    runs = [[1, 2, 3], [3, 4, 5]]                          # Mittel je Index: 2, 3, 4
    assert E.welch_curve(runs, 1) == pytest.approx([2.5, 3.0, 3.5])
    assert E.welch_curve(runs, 0) == pytest.approx([2.0, 3.0, 4.0])


def test_autocorrelation_by_hand():
    """x = 1..5: Mittel 3, Σ(x−x̄)² = 10; Lag 1: (−2·−1 + −1·0 + 0·1 + 1·2)/10 = 0.4."""
    assert E.autocorrelation([1, 2, 3, 4, 5], 2) == pytest.approx([0.4, -0.1])
    assert E.autocorrelation([5, 5, 5], 2) == [0.0, 0.0]


def test_covers():
    assert E.covers(10.0, 9.0, 1.0) and not E.covers(10.0, 9.0, 0.5) and E.covers(10.0, 10.0, 0.0)
