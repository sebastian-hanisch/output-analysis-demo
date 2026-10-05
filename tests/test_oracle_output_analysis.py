"""Orakel-Tests (unabhängiger Rechenweg, kleine Fassung des Scratchpad-Laufs mit 300 Zufallsinstanzen):
Lindley-Rekursion gegen die Abgangszeiten-Rekursion, MSER-5 gegen Vollsuche, Batch-Intervall/Autokorrelation/Welch gegen numpy/scipy,
stationärer Start gegen die Formel Kunde für Kunde."""

import math
import random

import pytest

import oa_estimators as E
import oa_formulas as F
import oa_simulation as S

np = pytest.importorskip("numpy")


def test_lindley_equals_the_departure_time_recursion():
    """W_k = max(0, D_{k-1} − T_k) mit D = Start + Bedienzeit, aus denselben Zufallsströmen: ein anderer Rechenweg als W' = max(0, W + S − A)."""
    rng = random.Random(1)
    for _ in range(60):
        rho, n, seed = rng.choice([10, 50, 90, 97]), rng.randint(1, 50), rng.randint(0, 10**6)
        speedup = rng.choice([0, 5, 50])
        lam, mu = rho / 100 * S.MU, S.MU * (1 + speedup / 100)
        g, s = S.SplitMix64(seed), S.SplitMix64(seed + 7_777_777)
        arrivals = np.cumsum([g.expovariate(lam) for _ in range(n)])
        service = [s.expovariate(mu) for _ in range(n)]
        ref, dep = [0.0], arrivals[0] + service[0]
        for k in range(1, n):
            start = max(arrivals[k], dep)
            ref.append(start - arrivals[k])
            dep = start + service[k]
        assert S.run_waits(rho, n, seed, speedup_pct=speedup) == pytest.approx(ref, abs=1e-9)


def test_stationary_start_has_the_formula_mean_for_every_customer_index():
    """Im Gleichgewicht ist jede Wartezeit (nicht nur die erste) verteilt wie die Formel: Mittel Wq und P(W = 0) = 1 − ρ."""
    n_runs = 6000
    runs = np.array([S.run_waits(50, 4, 500 + i, stationary_start=True) for i in range(n_runs)])
    truth = F.mean_wait(0.5 * S.MU, S.MU)
    for k in range(4):
        se = runs[:, k].std() / math.sqrt(n_runs)
        assert abs(runs[:, k].mean() - truth) < 4.5 * se
        assert abs((runs[:, k] == 0).mean() - 0.5) < 4.5 * 0.5 / math.sqrt(n_runs)


def test_estimators_against_numpy_and_a_brute_force_mser():
    stats = pytest.importorskip("scipy.stats")
    rng = random.Random(2)
    for _ in range(30):
        n = rng.randint(10, 200)
        x = np.array([rng.expovariate(1.0) for _ in range(n)])
        nb = rng.choice([2, 3, 5, 10])
        ref = x[:(n // nb) * nb].reshape(nb, -1).mean(1)
        mean, half = E.batch_means_interval(list(x), nb)
        assert mean == pytest.approx(ref.mean())
        assert half == pytest.approx(stats.t.ppf(0.975, nb - 1) * ref.std(ddof=1) / math.sqrt(nb), rel=2e-3)
        # MSER-5 per Vollsuche über alle zulässigen Abschneidepunkte
        y = x[:(n // 5) * 5].reshape(-1, 5).mean(1)
        best = None
        for d in range(0, int(0.5 * len(y)) + 1):
            r = y[d:]
            if len(r) < 2:
                break
            stat = ((r - r.mean()) ** 2).sum() / len(r) ** 2
            if best is None or stat < best[0] - 1e-15:
                best = (stat, d)
        assert E.mser_truncation(list(x)) == (best[1] * 5 if len(y) >= 2 else 0)
        # Autokorrelation und Welch-Mittelung
        lag = rng.randint(1, min(8, n - 1))
        xc = x - x.mean()
        assert E.autocorrelation(list(x), lag) == pytest.approx([(xc[:-l] * xc[l:]).sum() / (xc ** 2).sum() for l in range(1, lag + 1)])
        runs = [[rng.random() for _ in range(n)] for _ in range(rng.randint(1, 4))]
        w = rng.randint(0, 5)
        mean_idx = np.mean(runs, axis=0)
        ref_w = [mean_idx[max(0, k - w):min(n, k + w + 1)].mean() for k in range(n)]
        assert E.welch_curve(runs, w) == pytest.approx(ref_w)


def test_intervals_keep_their_nominal_coverage_on_independent_data():
    """Bei unabhängigen Normalwerten halten alle Intervallverfahren ihr Versprechen (anders als bei Wartezeiten)."""
    r = random.Random(5)
    hits = {"naive": 0, "batch": 0}
    reps = 800
    for _ in range(reps):
        x = [r.gauss(0, 1) for _ in range(200)]
        hits["naive"] += E.covers(0.0, *E.naive_interval(x))
        hits["batch"] += E.covers(0.0, *E.batch_means_interval(x, 20))
    assert all(0.92 < v / reps < 0.975 for v in hits.values()), hits
