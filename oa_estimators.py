"""Intervallschätzer und Warm-up-Verfahren als einzeln prüfbare Einheiten (je eine Regel, keine versteckten Zustände).

Alle Intervalle sind zweiseitig mit Nennniveau 95 %: Rückgabe (Mittelwert, Halbbreite)."""

import math
import statistics

# Quantil 0.975 der t-Verteilung (Standardtabelle); Freiheitsgrade 31..120 werden mit dem Wert der nächstkleineren
# Tabellenzeile angesetzt (leicht konservativ); ab 120 Freiheitsgraden gilt der Wert der Zeile 120 (1.980, knapp über dem
# Normalquantil 1.960).
_T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
         11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
         21: 2.080, 22: 2.074, 23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045, 30: 2.042,
         40: 2.021, 60: 2.000, 120: 1.980}
NORMAL_975 = 1.960


def t_quantile(df):
    """Quantil 0.975 der t-Verteilung mit `df` Freiheitsgraden (df ≥ 1)."""
    if df < 1:
        raise ValueError("Freiheitsgrade müssen ≥ 1 sein")
    if df <= 30:
        return _T975[df]
    for edge in (120, 60, 40):
        if df >= edge:
            return _T975[edge]
    return _T975[30]      # 31..39 (nächstkleinere Zeile)


def _interval_from_independent(values):
    """Mittel und Halbbreite t_{m−1} · s/√m aus m (als unabhängig behandelten) Werten."""
    m = len(values)
    return statistics.fmean(values), t_quantile(m - 1) * statistics.stdev(values) / math.sqrt(m)


def naive_interval(x):
    """Intervall, das alle Wartezeiten als unabhängig behandelt: s/√n. Falsch bei Autokorrelation - zu schmal."""
    return _interval_from_independent(x)


def batch_means(x, n_batches):
    """Mittelwerte von `n_batches` gleich langen, aufeinanderfolgenden Blöcken; ein Rest am Ende wird verworfen."""
    size = len(x) // n_batches
    if size < 1:
        raise ValueError("weniger Werte als Batches")
    return [sum(x[i * size:(i + 1) * size]) / size for i in range(n_batches)]


def batch_means_interval(x, n_batches):
    """Intervall aus den Batch-Mittelwerten: sie sind (bei langen Batches) fast unabhängig und fast normalverteilt."""
    return _interval_from_independent(batch_means(x, n_batches))


def replication_interval(replication_means):
    """Intervall aus den Mittelwerten unabhängiger Wiederholungen (jede mit eigenen Zufallsströmen)."""
    return _interval_from_independent(replication_means)


def delete_initial(x, fraction):
    """Die ersten `fraction` (0 ≤ f < 1) der Werte verwerfen (feste Warm-up-Regel)."""
    if not 0 <= fraction < 1:
        raise ValueError("Anteil muss in [0, 1) liegen")
    return x[int(len(x) * fraction):]


def mser_truncation(x, block=5, max_fraction=0.5):
    """MSER-5 (White 1997): Blockmittel der Länge `block` bilden und den Abschneidepunkt d wählen, der
    Σ_{j>d} (y_j − ȳ_d)² / (m − d)² minimiert (m = Zahl der Blöcke, d höchstens `max_fraction`·m). Rückgabe: Zahl der
    zu verwerfenden Einzelwerte (Vielfaches von `block`)."""
    y = [sum(x[i:i + block]) / block for i in range(0, len(x) - block + 1, block)]
    m = len(y)
    if m < 2:
        return 0
    suffix, suffix_sq = [0.0] * (m + 1), [0.0] * (m + 1)
    for j in range(m - 1, -1, -1):
        suffix[j] = suffix[j + 1] + y[j]
        suffix_sq[j] = suffix_sq[j + 1] + y[j] * y[j]
    best_stat, best_d = None, 0
    for d in range(0, int(max_fraction * m) + 1):
        rest = m - d
        if rest < 2:
            break
        stat = (suffix_sq[d] - suffix[d] ** 2 / rest) / (rest * rest)
        if best_stat is None or stat < best_stat:
            best_stat, best_d = stat, d
    return best_d * block


def welch_curve(runs, window):
    """Welch-Verfahren: Mittel über die Wiederholungen je Kundennummer, danach gleitender Mittelwert der Breite
    2·`window`+1 (am Rand schmaler). Zeigt, ab wann die Kurve einem Niveau zustrebt."""
    n = min(len(r) for r in runs)
    mean_by_index = [sum(r[k] for r in runs) / len(runs) for k in range(n)]
    out = []
    for k in range(n):
        lo, hi = max(0, k - window), min(n, k + window + 1)
        out.append(sum(mean_by_index[lo:hi]) / (hi - lo))
    return out


def autocorrelation(x, max_lag):
    """Stichproben-Autokorrelation für die Verzögerungen 1..max_lag."""
    n = len(x)
    mean = sum(x) / n
    var = sum((v - mean) ** 2 for v in x)
    if var == 0:
        return [0.0] * max_lag
    return [sum((x[i] - mean) * (x[i + lag] - mean) for i in range(n - lag)) / var for lag in range(1, max_lag + 1)]


def covers(truth, mean, half_width):
    """Ob das Intervall mean ± half_width den wahren Wert enthält."""
    return abs(mean - truth) <= half_width
