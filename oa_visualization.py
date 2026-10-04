"""Plotly-Abbildungen der Output-Analysis-Demo: Intervalle, Autokorrelation, Abdeckung, Welch-Plot, Warm-up-Strategien,
Pfade mit/ohne gemeinsame Zufallszahlen, Varianzfaktor. Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim
Scrollen nicht zoomen."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import oa_constants as C

GOOD_COLOR = "#54a24b"
BAD_COLOR = "#e45756"
TRUTH_COLOR = "#f58518"
SIM_COLOR = "#4c78a8"
METHOD_COLORS = {"naive": "#e45756", "batch5": "#9ecae1", "batch10": "#6baed6", "batch20": "#3182bd",
                 "batch30": "#08519c", "repl10": "#54a24b"}
STRATEGY_COLORS = {"none": "#7f7f7f", "del10": "#9ecae1", "del20": "#4c78a8", "del50": "#08519c", "mser": "#f58518",
                   "stat": "#54a24b"}


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height, legend_y=-0.25, top=10):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=top, b=10), legend=dict(orientation="h", y=legend_y),
                      plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_interval_chart(rows, truth):
    """Mittel ± Halbbreite je Methode (Punkt mit Fehlerbalken); grün, wenn das Intervall den wahren Wert enthält,
    sonst rot; gestrichelt der wahre Wert (Formel)."""
    fig = go.Figure()
    for row in rows:
        color = GOOD_COLOR if row["covers"] else BAD_COLOR
        fig.add_trace(go.Scatter(
            x=[row["mean"]], y=[row["label"]], mode="markers",
            marker=dict(color=color, size=11), error_x=dict(type="constant", value=row["half"], color=color, thickness=3),
            name=row["label"], showlegend=False,
            hovertemplate=f"{row['label']}<br>Mittel {row['mean']:.1f} min, ± {row['half']:.1f} min<extra></extra>"))
    fig.add_vline(x=truth, line=dict(color=TRUTH_COLOR, width=2, dash="dash"),
                  annotation_text=f"wahr (Formel) {truth:.1f} min", annotation_position="top")
    fig.update_xaxes(title_text="Mittlere Wartezeit (Minuten)", rangemode="tozero")
    fig.update_yaxes(autorange="reversed")
    return _base(fig, 230, top=30)


def build_acf_chart(acf):
    """Autokorrelation der Wartezeiten aufeinanderfolgender Lkw für die Verzögerungen 1, 2, ..."""
    lags = list(range(1, len(acf) + 1))
    fig = go.Figure(go.Bar(x=lags, y=acf, marker_color=SIM_COLOR, hovertemplate="Lag %{x}: %{y:.2f}<extra></extra>"))
    fig.update_xaxes(title_text="Abstand zwischen zwei Lkw in der Reihe (Lag)")
    fig.update_yaxes(title_text="Autokorrelation der Wartezeiten", range=[min(-0.1, min(acf) - 0.05), 1.0])
    return _base(fig, 250)


def build_coverage_chart(precomputed, n):
    """Abdeckung des nominalen 95-%-Intervalls je Methode über der Auslastung (Lauflänge n)."""
    fig = go.Figure()
    for method in C.METHOD_ORDER:
        rows = sorted((c for c in precomputed["coverage"] if c["n"] == n), key=lambda c: c["rho_pct"])
        fig.add_trace(go.Scatter(
            x=[c["rho_pct"] for c in rows], y=[c["variants"][method]["cover"] for c in rows], mode="lines+markers",
            line=dict(color=METHOD_COLORS[method], width=2.5), name=C.METHOD_LABELS[method],
            hovertemplate="ρ = %{x} %: %{y:.0%}<extra>" + C.METHOD_LABELS[method] + "</extra>"))
    fig.add_hline(y=0.95, line=dict(color="#888", width=1, dash="dot"), annotation_text="nominal 95 %",
                  annotation_position="top left")
    fig.update_xaxes(title_text="Auslastung ρ (%)", tickmode="array", tickvals=list(C.GRID_RHO_PCT))
    fig.update_yaxes(title_text="Anteil der Intervalle, die den wahren Wert enthalten", tickformat=".0%", range=[0, 1.02])
    return _base(fig, 380, legend_y=-0.3)


def build_welch_chart(curve, truth, deleted=0, mser_cut=0):
    """Welch-Plot: gleitendes Mittel über die Wiederholungen je Kundennummer; waagerecht der wahre Wert; senkrecht
    der gewählte Abschneidepunkt (Regler) und der MSER-5-Punkt des Hauptlaufs, soweit im gezeigten Bereich."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(1, len(curve) + 1)), y=curve, mode="lines", line=dict(color=SIM_COLOR, width=2.5),
                             name="Mittel über die Wiederholungen (geglättet)"))
    fig.add_hline(y=truth, line=dict(color=TRUTH_COLOR, width=2, dash="dash"), annotation_text=f"wahr {truth:.1f} min",
                  annotation_position="bottom right")
    if 0 < deleted < len(curve):
        fig.add_vline(x=deleted, line=dict(color=GOOD_COLOR, width=2), annotation_text="gelöscht bis hier",
                      annotation_position="top")
    if 0 < mser_cut < len(curve):
        fig.add_vline(x=mser_cut, line=dict(color="#7f3c8d", width=2, dash="dot"), annotation_text="MSER-5",
                      annotation_position="top left")
    fig.update_xaxes(title_text="Nummer des Lkw seit Start (leeres Gate)")
    fig.update_yaxes(title_text="Mittlere Wartezeit (Minuten)", rangemode="tozero")
    return _base(fig, 320, top=30)


def build_warmup_chart(precomputed, rho_pct):
    """Zwei Bilder: mittlere Abweichung vom wahren Wert (Startverzerrung) und Abdeckung je Warm-up-Strategie über der
    Lauflänge, für eine gemessene Auslastung."""
    cells = sorted((c for c in precomputed["coverage"] if c["rho_pct"] == rho_pct), key=lambda c: c["n"])
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Abweichung vom wahren Wert (%)",
                                                        "Abdeckung des 95-%-Intervalls"), horizontal_spacing=0.12)
    for strategy in C.WARMUP_ORDER:
        ns = [c["n"] for c in cells]
        label = C.WARMUP_LABELS[strategy]
        fig.add_trace(go.Scatter(x=ns, y=[c["variants"][strategy]["bias_pct"] for c in cells], mode="lines+markers",
                                 line=dict(color=STRATEGY_COLORS[strategy], width=2), name=label, legendgroup=strategy),
                      row=1, col=1)
        fig.add_trace(go.Scatter(x=ns, y=[c["variants"][strategy]["cover"] for c in cells], mode="lines+markers",
                                 line=dict(color=STRATEGY_COLORS[strategy], width=2), name=label, legendgroup=strategy,
                                 showlegend=False), row=1, col=2)
    ticks = list(C.GRID_N)
    ticktext = [f"{n // 1000}k" for n in ticks]
    for col in (1, 2):
        fig.update_xaxes(title_text="Lkw je Lauf (log)", type="log", tickmode="array", tickvals=ticks, ticktext=ticktext,
                         row=1, col=col)
    fig.update_yaxes(title_text="Abweichung (%)", row=1, col=1)
    fig.update_yaxes(title_text="Abdeckung", tickformat=".0%", range=[0, 1.02], row=1, col=2)
    _base(fig, 420, legend_y=-0.3)
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    return fig


def build_crn_paths(a, b_crn, b_ind, speedup_pct):
    """Wartezeitpfade zweier Systeme (B um `speedup_pct` % schneller): oben mit gemeinsamen, unten mit unabhängigen
    Zufallszahlen."""
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                        subplot_titles=("gemeinsame Zufallszahlen", "unabhängige Zufallszahlen"))
    x = list(range(1, len(a) + 1))
    for row, b in ((1, b_crn), (2, b_ind)):
        fig.add_trace(go.Scatter(x=x, y=a, mode="lines", line=dict(color=SIM_COLOR, width=1.8), name="System A",
                                 legendgroup="a", showlegend=row == 1), row=row, col=1)
        fig.add_trace(go.Scatter(x=x, y=b, mode="lines", line=dict(color=TRUTH_COLOR, width=1.8),
                                 name=f"System B ({speedup_pct} % schneller)", legendgroup="b", showlegend=row == 1),
                      row=row, col=1)
    fig.update_xaxes(title_text="Nummer des Lkw", row=2, col=1)
    fig.update_yaxes(title_text="Wartezeit (min)", row=1, col=1)
    fig.update_yaxes(title_text="Wartezeit (min)", row=2, col=1)
    _base(fig, 420, legend_y=-0.18)
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10))
    return fig


def build_crn_factor_chart(precomputed):
    """Varianzfaktor (Streuung der Differenz ohne gegenüber mit gemeinsamen Zufallszahlen) über der Auslastung."""
    fig = go.Figure()
    palette = ["#9ecae1", "#4c78a8", "#f58518", "#e45756"]
    for color, sp in zip(palette, C.CRN_SPEEDUPS):
        rows = sorted((c for c in precomputed["crn"] if c["speedup_pct"] == sp), key=lambda c: c["rho_pct"])
        fig.add_trace(go.Scatter(x=[c["rho_pct"] for c in rows], y=[c["variance_factor"] for c in rows],
                                 mode="lines+markers", line=dict(color=color, width=2.5),
                                 name=f"{sp} % schneller",
                                 hovertemplate="ρ = %{x} %: Faktor %{y:.1f}<extra>" + f"{sp} % schneller</extra>"))
    fig.add_hline(y=1, line=dict(color="#888", width=1, dash="dot"), annotation_text="kein Gewinn",
                  annotation_position="bottom right")
    ticks = [1, 2, 5, 10, 20, 50, 100]
    fig.update_xaxes(title_text="Auslastung ρ des Systems A (%)", tickmode="array", tickvals=list(C.GRID_RHO_PCT))
    fig.update_yaxes(title_text="Varianzfaktor (log)", type="log", tickmode="array", tickvals=ticks,
                     ticktext=[str(t) for t in ticks])
    return _base(fig, 340)
