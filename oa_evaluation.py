"""Auswertung: Intervall-Abdeckung, Warm-up-Strategien und gemeinsame Zufallszahlen auf der M/M/1-Schlange.
Die teuren Messreihen (Hunderte Läufe je Zelle) stehen vorgerechnet in `precomputed_sweep.json`
(Generator: generate_precomputed.py, Laden: `load_precomputed`); live läuft nur der gewählte Einzellauf."""

import json
import statistics
from pathlib import Path

import oa_constants as C
import oa_estimators as E
import oa_formulas as F
from oa_simulation import MU, run_waits

PRECOMPUTED_PATH = Path(__file__).resolve().parent / "precomputed_sweep.json"


def rates(rho_pct):
    """(λ, μ) je Minute bei Auslastung `rho_pct` (%) und 3 min mittlerer Abfertigung."""
    return rho_pct / 100.0 * MU, MU


def true_wait(rho_pct):
    """Wahre mittlere Wartezeit (Formel) in Minuten."""
    lam, mu = rates(rho_pct)
    return F.mean_wait(lam, mu)


def replication_means(rho_pct, n_total, seed, n_reps=C.N_REPLICATIONS, delete_fraction=0.0):
    """Mittelwerte von `n_reps` unabhängigen Wiederholungen mit je n_total/n_reps Lkw (leerer Start, eigene Ströme je
    Wiederholung); optional werden je Wiederholung die ersten `delete_fraction` verworfen."""
    length = n_total // n_reps
    means = []
    for j in range(n_reps):
        x = run_waits(rho_pct, length, seed + 1000 * j + 5)
        means.append(statistics.fmean(E.delete_initial(x, delete_fraction)))
    return means


def single_run_report(rho_pct, n, seed, batches, warmup_pct):
    """Ein Lauf, drei Intervalle (naiv, Batch Means, unabhängige Wiederholungen) nach Verwerfen der ersten
    `warmup_pct` % (bei den Wiederholungen je Wiederholung), gegen den wahren Wert. Rückgabe: Dict mit dem wahren Wert,
    den Intervallen (key, label, mean, half, covers), den Wartezeiten des Hauptlaufs, ihrer Autokorrelation und dem
    MSER-5-Abschneidepunkt."""
    truth = true_wait(rho_pct)
    frac = warmup_pct / 100.0
    x = run_waits(rho_pct, n, seed)
    xd = E.delete_initial(x, frac)
    rows = []
    for key, label, (mean, half) in (
        ("naive", "naiv (alle Wartezeiten als unabhängig)", E.naive_interval(xd)),
        ("batch", f"Batch Means, {batches} Batches", E.batch_means_interval(xd, batches)),
        ("repl", f"{C.N_REPLICATIONS} unabhängige Wiederholungen", E.replication_interval(
            replication_means(rho_pct, n, seed, delete_fraction=frac))),
    ):
        rows.append({"key": key, "label": label, "mean": mean, "half": half, "covers": E.covers(truth, mean, half)})
    return {"truth": truth, "rows": rows, "waits": x, "acf": E.autocorrelation(x, C.ACF_LAGS),
            "mser_cut": E.mser_truncation(x)}


def welch_report(rho_pct, seed):
    """Welch-Plot live: Mittel über `WELCH_REPS` Wiederholungen von `WELCH_N` Lkw (leerer Start), geglättet."""
    runs = [run_waits(rho_pct, C.WELCH_N, seed + 31 * j) for j in range(C.WELCH_REPS)]
    return E.welch_curve(runs, C.WELCH_WINDOW)


def crn_paths(rho_pct, speedup_pct, seed, n=C.PATH_SHOWN):
    """Wartezeitpfade der ersten `n` Lkw: System A, System B (um `speedup_pct` % schneller) mit gemeinsamen
    Zufallszahlen und System B mit unabhängigen Zufallszahlen. Alle mit leerem Start."""
    a = run_waits(rho_pct, n, seed)
    b_crn = run_waits(rho_pct, n, seed, speedup_pct=speedup_pct)
    b_ind = run_waits(rho_pct, n, seed + 999_983, speedup_pct=speedup_pct)
    return a, b_crn, b_ind


def _summarise(point_estimates, covers_flags, half_widths, truth):
    """Abdeckung, mittlere Abweichung (%), relative Streuung eines Laufs und mittlere relative Halbbreite."""
    mean_est = statistics.fmean(point_estimates)
    return {"cover": sum(covers_flags) / len(covers_flags), "bias_pct": 100.0 * (mean_est - truth) / truth,
            "rel_std": statistics.stdev(point_estimates) / truth, "rel_half": statistics.fmean(half_widths) / truth}


def coverage_study(rho_pct, n, reps, seed_base):
    """Über `reps` unabhängige Läufe: wie oft enthält das 95-%-Intervall den wahren Wert, wie verzerrt und wie breit
    ist es, je Methode und Warm-up-Strategie. Läufe starten leer, außer 'stat' (Start im Gleichgewicht)."""
    truth = true_wait(rho_pct)
    acc = {}

    def add(name, interval):
        mean, half = interval
        acc.setdefault(name, ([], [], []))
        acc[name][0].append(mean)
        acc[name][1].append(E.covers(truth, mean, half))
        acc[name][2].append(half)

    for r in range(reps):
        seed = seed_base + 97 * r
        x = run_waits(rho_pct, n, seed)
        add("naive", E.naive_interval(x))
        for b in C.BATCH_OPTIONS:
            add(f"batch{b}", E.batch_means_interval(x, b))
        add("del10", E.batch_means_interval(E.delete_initial(x, 0.10), 20))
        add("del20", E.batch_means_interval(E.delete_initial(x, 0.20), 20))
        add("del50", E.batch_means_interval(E.delete_initial(x, 0.50), 20))
        add("mser", E.batch_means_interval(x[E.mser_truncation(x):], 20))
        xs = run_waits(rho_pct, n, seed, stationary_start=True)
        add("stat", E.batch_means_interval(xs, 20))
        add("naive_stat", E.naive_interval(xs))
        add("repl10", E.replication_interval(replication_means(rho_pct, n, seed)))
        add("repl10_del20", E.replication_interval(replication_means(rho_pct, n, seed, delete_fraction=0.2)))
    cell_ = {name: _summarise(*vals, truth) for name, vals in acc.items()}
    cell_["none"] = cell_["batch20"]       # "nichts löschen" ist der Batch-Means-Lauf mit 20 Batches
    return {"rho_pct": rho_pct, "n": n, "reps": reps, "truth": truth, "variants": cell_}


def crn_study(rho_pct, speedup_pct, n, reps, seed_base):
    """Vergleich zweier Systeme (B um `speedup_pct` % schneller): Streuung der geschätzten Wartezeit-Differenz mit
    gemeinsamen Zufallszahlen gegen unabhängige Läufe. Beide Systeme starten im Gleichgewicht (keine Startverzerrung)."""
    truth_diff = true_wait(rho_pct) - F.mean_wait(rates(rho_pct)[0], MU * (1 + speedup_pct / 100.0))
    d_crn, d_ind = [], []
    for r in range(reps):
        seed = seed_base + 97 * r
        a = statistics.fmean(run_waits(rho_pct, n, seed, stationary_start=True))
        d_crn.append(a - statistics.fmean(run_waits(rho_pct, n, seed, stationary_start=True, speedup_pct=speedup_pct)))
        d_ind.append(a - statistics.fmean(run_waits(rho_pct, n, seed + 999_983, stationary_start=True,
                                                    speedup_pct=speedup_pct)))
    sd_crn, sd_ind = statistics.stdev(d_crn), statistics.stdev(d_ind)
    return {"rho_pct": rho_pct, "speedup_pct": speedup_pct, "n": n, "reps": reps, "truth_diff": truth_diff,
            "mean_crn": statistics.fmean(d_crn), "mean_ind": statistics.fmean(d_ind), "sd_crn": sd_crn,
            "sd_ind": sd_ind, "variance_factor": (sd_ind / sd_crn) ** 2}


def load_precomputed():
    with open(PRECOMPUTED_PATH, encoding="utf-8") as f:
        return json.load(f)


def nearest_grid_rho(rho_pct):
    """Nächste gemessene Auslastung der vorgerechneten Tabelle (bei Gleichstand die kleinere)."""
    return min(C.GRID_RHO_PCT, key=lambda g: (abs(g - rho_pct), g))


def warmup_summary(precomputed, tolerance=0.03):
    """Über alle gemessenen Zellen (Auslastung × Lauflänge): in wie vielen weicht die Abdeckung einer Warm-up-Strategie um
    mehr als `tolerance` von 'nichts löschen' ab, dazu die höchste Abdeckung des naiven Intervalls (mit leerem Start
    und mit Start im Gleichgewicht)."""
    cells = [c["variants"] for c in precomputed["coverage"]]

    def worse(key):
        return sum(1 for v in cells if v[key]["cover"] < v["none"]["cover"] - tolerance)

    def better(key):
        return sum(1 for v in cells if v[key]["cover"] > v["none"]["cover"] + tolerance)

    return {"total": len(cells), "mser_worse": worse("mser"), "mser_better": better("mser"),
            "del20_changed": worse("del20") + better("del20"), "stat_worse": worse("stat"), "stat_better": better("stat"),
            "naive_max": max(v["naive"]["cover"] for v in cells), "naive_stat_max": max(v["naive_stat"]["cover"] for v in cells)}


def coverage_cell(precomputed, rho_pct, n):
    """Zelle der Abdeckungs-Tabelle für (gemessene Auslastung, Lauflänge)."""
    return next(c for c in precomputed["coverage"] if c["rho_pct"] == rho_pct and c["n"] == n)
