"""Simulation: Generator, Lindley-Rekursion an der Drei-Lkw-Instanz, stationärer Start, gemeinsame Zufallszahlen."""

import math

import pytest

import oa_formulas as F
import oa_simulation as S
from conftest import ScriptedRng


def test_splitmix64_matches_the_reference_sequence():
    rng = S.SplitMix64(0)
    assert [rng.next() for _ in range(3)] == [0xE220A8397B1DCDAF, 0x6E789E6AA1B965F4, 0x06C45D188009454F]


def test_expovariate_is_positive_with_the_right_mean():
    rng = S.SplitMix64(5)
    ex = [rng.expovariate(0.5) for _ in range(20000)]
    assert min(ex) > 0 and sum(ex) / len(ex) == pytest.approx(2.0, rel=0.05)


def test_lindley_step_by_hand():
    assert S.lindley_step(0.0, 2.0, 1.5) == 0.5 and S.lindley_step(0.5, 1.0, 3.0) == 0.0


def test_waits_on_the_three_truck_instance(mini_streams):
    gap, svc = mini_streams
    assert S.waits(0.5, 0.5, 3, gap, svc) == pytest.approx([0.0, 0.5, 1.5])


def test_stationary_wait_is_zero_when_the_first_uniform_is_above_rho():
    rng = ScriptedRng(uniform_values=[0.95, 0.5])
    assert S.draw_stationary_wait(0.3, 1 / 3, rng) == 0.0 and rng.n_uniform == 2     # zieht trotzdem beide Zahlen


def test_stationary_wait_by_hand_when_busy():
    """ρ = 0.9, u_busy = 0.5 < ρ, u_len = 0.5: Wartezeit = −ln(0.5)/(μ−λ)."""
    rng = ScriptedRng(uniform_values=[0.5, 0.5])
    assert S.draw_stationary_wait(0.3, 1 / 3, rng) == pytest.approx(math.log(2) / (1 / 3 - 0.3))


def test_stationary_start_draws_the_wait_of_the_first_customer(mini_streams):
    gap, svc = mini_streams
    gap.uniform_values = [0.2, 0.5]                      # 0.2 < ρ = 0.5: Kunde 1 wartet ln2/(μ−λ) = ln2/0.25
    out = S.waits(0.25, 0.5, 3, gap, svc, stationary_start=True)
    assert out[0] == pytest.approx(math.log(2) / 0.25)
    assert gap.n_uniform == 2


def test_first_customer_wait_in_equilibrium_has_the_formula_mean():
    lam, mu = 0.5 * S.MU, S.MU
    first = [S.waits(lam, mu, 1, S.SplitMix64(s), S.SplitMix64(s + 1), stationary_start=True)[0] for s in range(6000)]
    assert sum(first) / len(first) == pytest.approx(F.mean_wait(lam, mu), rel=0.1)


def test_long_equilibrium_run_matches_the_formula():
    x = S.run_waits(50, 200_000, 1, stationary_start=True)
    assert sum(x) / len(x) == pytest.approx(3.0, rel=0.04)


def test_same_seed_same_result_and_speedup_zero_changes_nothing():
    a = S.run_waits(90, 500, 11)
    assert a == S.run_waits(90, 500, 11) and a != S.run_waits(90, 500, 12)
    assert a == S.run_waits(90, 500, 11, speedup_pct=0)


def test_common_random_numbers_make_the_faster_system_never_wait_longer_customer_by_customer():
    """Gleiche Ankünfte und (skalierte) gleiche Bedienzeiten: die Lindley-Rekursion ist monoton, also gilt W_B ≤ W_A
    für jeden einzelnen Kunden - im Gegensatz zu unabhängigen Zufallszahlen."""
    a = S.run_waits(90, 3000, 7)
    b = S.run_waits(90, 3000, 7, speedup_pct=10)
    assert all(wb <= wa + 1e-9 for wa, wb in zip(a, b))
    b_ind = S.run_waits(90, 3000, 7 + 999_983, speedup_pct=10)
    assert any(wb > wa for wa, wb in zip(a, b_ind))


def test_service_stream_is_separate_from_the_arrival_stream():
    a = S.run_waits(90, 300, 3, service_seed=100)
    b = S.run_waits(90, 300, 3, service_seed=101)
    assert a != b and a[0] == b[0] == 0.0
