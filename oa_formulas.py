"""Geschlossene Formeln der M/M/1-Schlange (Kopie aus mm1-queue-demo, Stück 1 - bewusst ohne Import zwischen Repos).
Zeiten in Minuten, Raten je Minute. Nur für ρ = λ/μ < 1."""


def mean_wait(lam, mu):
    """Mittlere Wartezeit in der Schlange Wq = ρ/(μ−λ): der WAHRE Wert, gegen den die Intervalle dieser Demo antreten."""
    if lam >= mu:
        raise ValueError("ρ ≥ 1: keine stationäre Verteilung")
    return (lam / mu) / (mu - lam)


def prob_wait(lam, mu):
    """P(Wq > 0) = ρ."""
    return lam / mu
