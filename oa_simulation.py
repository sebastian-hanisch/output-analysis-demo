"""Wartezeiten einer M/M/1-Schlange (FIFO, ein Server) per Lindley-Rekursion W_{k+1} = max(0, W_k + S_k − A_{k+1}).

In mm1-queue-demo (Stück 1) ist gezeigt, dass die Lindley-Rekursion Kunde für Kunde dieselben Wartezeiten liefert wie
die Ereignissimulation; hier dient sie als schneller Erzeuger des Ausgabeprozesses (Wartezeit je Kunde).

Zufall nur über übergebene `SplitMix64`-Generatoren (reine Ganzzahl-Arithmetik, Portfolio-Konvention). Ankünfte und
Bedienzeiten haben je einen EIGENEN Strom: gleiche Ankunftsströme in zwei Systemen sind dann gemeinsame Zufallszahlen
(common random numbers), ohne dass die Bedienzeiten mitlaufen müssen."""

import math

_MASK = (1 << 64) - 1
MEAN_SERVICE_MIN = 3.0          # mittlere Abfertigungsdauer (Minuten) in allen Läufen der Demo
MU = 1.0 / MEAN_SERVICE_MIN


class SplitMix64:
    """Kleiner, gut gemischter 64-Bit-Zufallsgenerator (Vigna); reine Ganzzahl-Arithmetik."""

    def __init__(self, seed):
        self.state = seed & _MASK

    def next(self):
        self.state = (self.state + 0x9E3779B97F4A7C15) & _MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK
        return z ^ (z >> 31)

    def uniform(self):
        """Gleichverteilt auf [0, 1) mit 53 Bit."""
        return (self.next() >> 11) * (1.0 / (1 << 53))

    def expovariate(self, rate):
        """Exponentiell mit Mittel 1/rate (Inversion; 1 − u liegt in (0, 1], der Logarithmus ist endlich)."""
        return -math.log(1.0 - self.uniform()) / rate


def draw_stationary_wait(lam, mu, rng):
    """Wartezeit eines Kunden im Gleichgewicht: 0 mit Wahrscheinlichkeit 1−ρ, sonst exponentiell mit Rate μ−λ
    (P(Wq > t) = ρ e^{−(μ−λ)t}). Zieht IMMER zwei Zufallszahlen, damit zwei Systeme mit demselben Strom im Gleichschritt
    bleiben (Voraussetzung für gemeinsame Zufallszahlen)."""
    u_busy, u_len = rng.uniform(), rng.uniform()
    if u_busy >= lam / mu:
        return 0.0
    return -math.log(1.0 - u_len) / (mu - lam)


def lindley_step(wait, service, gap):
    """Wartezeit des nächsten Kunden: W' = max(0, W + S − A)."""
    return max(0.0, wait + service - gap)


def waits(lam, mu, n, gap_rng, svc_rng, stationary_start=False):
    """Wartezeiten der ersten `n` Kunden. Start leer (erster Kunde wartet 0) oder im Gleichgewicht (Wartezeit des ersten
    Kunden aus der stationären Verteilung gezogen - nur möglich, weil für M/M/1 die Formel bekannt ist)."""
    w = draw_stationary_wait(lam, mu, gap_rng) if stationary_start else 0.0
    out = [0.0] * n
    prev_service = 0.0
    for k in range(n):
        gap = gap_rng.expovariate(lam)
        if k > 0:
            w = lindley_step(w, prev_service, gap)
        out[k] = w
        prev_service = svc_rng.expovariate(mu)
    return out


def run_waits(rho_pct, n, seed, stationary_start=False, speedup_pct=0, service_seed=None):
    """Ein Lauf bei Auslastung `rho_pct` (%): Ankünfte aus `seed`, Bedienzeiten aus `service_seed` (Standard: aus
    `seed` abgeleitet). `speedup_pct`: Abfertigung um so viel Prozent schneller bei gleichen Ankünften (zweites System
    eines Vergleichs). Rückgabe: Wartezeiten je Kunde."""
    lam = rho_pct / 100.0 * MU
    mu = MU * (1 + speedup_pct / 100.0)
    gap_rng = SplitMix64(seed)
    svc_rng = SplitMix64(service_seed if service_seed is not None else seed + 7_777_777)
    return waits(lam, mu, n, gap_rng, svc_rng, stationary_start)
