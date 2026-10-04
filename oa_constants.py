"""Konstanten der Output-Analysis-Demo: Regler, Voreinstellungen, Messreihen-Parameter."""


def fmt_int(n):
    """Ganzzahl mit Punkt als Tausendertrenner (10000 -> 10.000)."""
    return f"{n:,}".replace(",", ".")


def fmt_pct(x):
    """Anteil als ganze Prozent mit Leerzeichen (0.86 -> "86 %")."""
    return f"{x:.0%}".replace("%", " %")


RHO_PCT_MIN, RHO_PCT_MAX, DEFAULT_RHO_PCT = 10, 97, 90      # Auslastung ρ in Prozent (nur Gleichgewichtsfälle)
N_OPTIONS = (1000, 2000, 5000, 10000, 20000, 50000)         # Lkw je Lauf
DEFAULT_N = 10000
BATCH_OPTIONS = (5, 10, 20, 30)
DEFAULT_BATCHES = 20
WARMUP_PCT_MIN, WARMUP_PCT_MAX, WARMUP_PCT_STEP, DEFAULT_WARMUP_PCT = 0, 50, 5, 0
SEED_MAX = 999999
DEFAULT_SEED = 35
N_REPLICATIONS = 10               # Wiederholungen der Wiederholungs-Methode (je N/10 Lkw)
ACF_LAGS = 40

# Welch-Plot live: Wiederholungen × Lkw je Wiederholung, Glättungsfenster
WELCH_REPS, WELCH_N, WELCH_WINDOW = 50, 2000, 25
# Gemeinsame Zufallszahlen live: erste so viele Lkw des Pfadvergleichs
PATH_SHOWN = 300

# Vorgerechnete Messreihen (generate_precomputed.py)
GRID_RHO_PCT = (50, 70, 80, 90, 95)
GRID_N = N_OPTIONS
GRID_REPS = 400
CRN_N = 10000
CRN_SPEEDUPS = (5, 10, 20, 50)
CRN_REPS = 400

METHOD_ORDER = ("naive", "batch5", "batch10", "batch20", "batch30", "repl10")
METHOD_LABELS = {
    "naive": "naiv (alle Wartezeiten als unabhängig)",
    "batch5": "Batch Means, 5 Batches",
    "batch10": "Batch Means, 10 Batches",
    "batch20": "Batch Means, 20 Batches",
    "batch30": "Batch Means, 30 Batches",
    "repl10": "10 unabhängige Wiederholungen",
}
WARMUP_ORDER = ("none", "del10", "del20", "del50", "mser", "stat")
WARMUP_LABELS = {
    "none": "nichts löschen",
    "del10": "erste 10 % löschen",
    "del20": "erste 20 % löschen",
    "del50": "erste 50 % löschen",
    "mser": "MSER-5 (automatisch)",
    "stat": "Start im Gleichgewicht (nur mit Formel möglich)",
}

PRESET_ORDER = ("Normalfall (ρ = 90 %)", "Entspannt (ρ = 50 %)", "Fast voll (ρ = 95 %)", "Kurzer Lauf (1 000 Lkw)")


def _preset(rho_pct=DEFAULT_RHO_PCT, n=DEFAULT_N, batches=DEFAULT_BATCHES, warmup_pct=DEFAULT_WARMUP_PCT):
    return {"rho_pct": rho_pct, "n": n, "batches": batches, "warmup_pct": warmup_pct, "seed": DEFAULT_SEED}


PRESETS = {
    "Normalfall (ρ = 90 %)": _preset(),
    "Entspannt (ρ = 50 %)": _preset(rho_pct=50),
    "Fast voll (ρ = 95 %)": _preset(rho_pct=95, n=50000),
    "Kurzer Lauf (1 000 Lkw)": _preset(n=1000),
}
# Zahlen aus der vorgerechneten Messreihe (400 Läufe je Zelle); tests/test_claims.py rechnet sie nach
PRESET_HELP = {
    "Normalfall (ρ = 90 %)": "ρ = 90 %, 10 000 Lkw: Das naive 95-%-Intervall enthält den wahren Wert nur in 9 % der Fälle, Batch Means mit 20 Batches in 86 %.",
    "Entspannt (ρ = 50 %)": "ρ = 50 %, 10 000 Lkw: Selbst bei niedriger Auslastung trifft das naive Intervall nur in 49 % der Fälle, Batch Means (20) in 93 %.",
    "Fast voll (ρ = 95 %)": "ρ = 95 %, 50 000 Lkw: Auch der lange Lauf reicht noch nicht: Batch Means (20) trifft in 85 % der Fälle statt der versprochenen 95 %.",
    "Kurzer Lauf (1 000 Lkw)": "ρ = 90 %, nur 1 000 Lkw: Batch Means mit 20 Batches trifft in 55 % der Fälle, mit 5 längeren Batches in 74 %.",
}
