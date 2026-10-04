"""Output Analysis - wie viel Vertrauen verdient eine Simulation? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Zweites Stück der Konzepte-Linie "Warteschlangentheorie und Simulation": Ein Simulationslauf liefert einen Mittelwert,
aber wie genau ist er? Auf dem M/M/1-Gate aus Stück 1 (wahrer Wert aus der Formel bekannt) tritt jedes Verfahren gegen
den wahren Wert an: naives Intervall, Batch Means, unabhängige Wiederholungen, Warm-up-Regeln und gemeinsame
Zufallszahlen. Siehe README für die Einordnung in die Linie.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import oa_constants as C
from oa_evaluation import (coverage_cell, crn_paths, load_precomputed, nearest_grid_rho, single_run_report,
                           warmup_summary, welch_report)
from oa_presets import (apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_seed,
                        sync_query_params)
from oa_visualization import (build_acf_chart, build_coverage_chart, build_crn_factor_chart, build_crn_paths,
                              build_interval_chart, build_warmup_chart, build_welch_chart)

st.set_page_config(page_title="Output Analysis – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _precomputed():
    return load_precomputed()


@st.cache_data(show_spinner=False)
def _report(rho_pct, n, seed, batches, warmup_pct):
    return single_run_report(rho_pct, n, seed, batches, warmup_pct)


@st.cache_data(show_spinner=False)
def _welch(rho_pct, seed):
    return welch_report(rho_pct, seed)


@st.cache_data(show_spinner=False)
def _paths(rho_pct, speedup_pct, seed):
    return crn_paths(rho_pct, speedup_pct, seed)


st.title("📏 Output Analysis: wie viel Vertrauen verdient eine Simulation?")
st.markdown(
    """
Ein Simulationslauf liefert **einen** Mittelwert, und der ist nur eine Stichprobe. Ein **Konfidenzintervall** soll sagen,
wie weit er vom wahren Wert entfernt sein kann: ein 95-%-Intervall verspricht, dass 19 von 20 solcher Intervalle den
wahren Wert enthalten. Auf dem **M/M/1-Gate** ist der wahre Wert aus der Formel bekannt, deshalb lässt sich hier messen,
**ob die Versprechen halten**: für das **naive Intervall** (das alle Wartezeiten als unabhängig behandelt), für
**Batch Means** und für **unabhängige Wiederholungen**, dazu für verschiedene **Warm-up-Regeln** (was vom leeren Start
muss weg?) und für **gemeinsame Zufallszahlen** beim Vergleich zweier Systeme.
"""
)
st.caption(
    "Zweites Stück der Linie „Warteschlangentheorie und Simulation“, aufbauend auf "
    "[mm1-queue-demo](https://sebastianhanisch-mm1-queue-demo.streamlit.app/): dort streut ein Lauf um die Formel, hier die "
    "Frage, wie man diese Streuung ehrlich angibt. Jedes Folgestück hebt eine der Annahmen unter „Wo die Annahmen "
    "enden“ auf."
)

with st.expander("So funktioniert die Intervallschätzung", expanded=True):
    st.markdown(
        """
- **Das Problem:** Die Wartezeiten aufeinanderfolgender Lkw sind **stark verwandt** (ein Rückstau trifft viele
  Nachfolger). Das Mittel von 10 000 solcher Zahlen ist deshalb viel unsicherer als das Mittel von 10 000 unabhängigen.
- **Naives Intervall:** rechnet mit s/√n, als wären alle Werte unabhängig. Zu schmal, sobald sie es nicht sind.
- **Batch Means:** den Lauf in Blöcke (Batches) teilen und die **Blockmittel** wie unabhängige Werte behandeln. Das
  klappt, wenn die Blöcke länger sind als die „Erinnerung“ des Systems.
- **Unabhängige Wiederholungen:** mehrere kürzere Läufe mit eigenen Zufallszahlen, jeder startet leer. Echte Unabhängigkeit,
  aber jeder Lauf trägt den Einschwing-Fehler des leeren Starts mit.
- **Warm-up:** Der leere Start unterschätzt die Schlange zu Beginn. Mögliche Gegenmittel: den Anfang löschen (fester Anteil
  oder automatisch per MSER-5) oder, wo man den Gleichgewichtszustand kennt, dort starten.
- **Gemeinsame Zufallszahlen:** Zwei Systeme mit denselben Ankünften vergleichen, damit Zufallsunterschiede sich
  herauskürzen.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
preset_cols = st.columns(len(C.PRESET_ORDER))
for i, name in enumerate(C.PRESET_ORDER):
    with preset_cols[i]:
        st.button(name, key=f"preset_{name}", width="stretch", on_click=apply_preset, args=(name,),
                  help=C.PRESET_HELP[name])

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    rho_pct = st.slider("Auslastung ρ des Gates", *bounds("rho_slider"), key="rho_slider", format="%d %%",
                        help="Anteil der Zeit, in dem die Spur im Mittel belegt ist. Nur Gleichgewichtsfälle "
                             "(unter 100 %): nur dort gibt es einen wahren Wert zum Vergleichen.")
    n = st.select_slider("Simulierte Lkw je Lauf", options=C.N_OPTIONS, key="n_select",
                         help="Länge des Hauptlaufs; die unabhängigen Wiederholungen teilen sie in "
                              f"{C.N_REPLICATIONS} gleich lange Läufe.")
    batches = st.select_slider("Batches (Batch Means)", options=C.BATCH_OPTIONS, key="batches_select",
                               help="Zahl der Blöcke, in die der Lauf für Batch Means geteilt wird.")
    warmup_pct = st.slider("Anfang löschen (Warm-up)", *bounds("warmup_slider"), step=C.WARMUP_PCT_STEP,
                           key="warmup_slider", format="%d %%",
                           help="Anteil der ersten Lkw, der vor der Auswertung verworfen wird (bei den Wiederholungen "
                                "je Wiederholung).")
    seed = st.number_input("Zufalls-Seed", min_value=bounds("seed_input")[0], max_value=bounds("seed_input")[1],
                           step=1, key="seed_input", help="Bestimmt alle Zufallszahlen des Laufs.")
    st.button("🎲 Neuen Lauf würfeln", on_click=randomize_seed)

rho_pct, n, batches, warmup_pct, seed = int(rho_pct), int(n), int(batches), int(warmup_pct), int(seed)
sync_query_params({"rho_slider": rho_pct, "n_select": n, "batches_select": batches, "warmup_slider": warmup_pct,
                   "seed_input": seed})

pre = _precomputed()
grid_rho = nearest_grid_rho(rho_pct)
cell = coverage_cell(pre, grid_rho, n)["variants"]

with st.spinner("Simuliere …"):
    report = _report(rho_pct, n, seed, batches, warmup_pct)
truth = report["truth"]

st.markdown("---")
st.markdown("## 📏 Ein Lauf, drei Intervalle")
st.caption(
    f"Gate bei ρ = {rho_pct} %, mittlere Abfertigung 3 min: der wahre Wert der mittleren Wartezeit ist "
    f"**{truth:.1f} min** (Formel). Hauptlauf mit {C.fmt_int(n)} Lkw, {warmup_pct} % davon vorab gelöscht."
)
cols = st.columns(3)
for col, row in zip(cols, report["rows"]):
    col.metric(row["label"], f"{row['mean']:.1f} ± {row['half']:.1f} min",
               delta="✅ enthält den wahren Wert" if row["covers"] else "❌ verfehlt den wahren Wert",
               delta_color="off", delta_arrow="off")
st.plotly_chart(build_interval_chart(report["rows"], truth), width="stretch",
                key=f"intervals_{rho_pct}_{n}_{seed}_{batches}_{warmup_pct}")
st.info(
    "**Ein einzelner Lauf sagt nur: dieses Intervall hat getroffen oder nicht.** Ob ein 95-%-Intervall sein "
    "Versprechen hält, zeigt erst die Abdeckung über viele Läufe (nächster Abschnitt)."
)

col_a, col_b = st.columns(2)
with col_a:
    st.markdown("**Warum das naive Intervall zu schmal ist: die Wartezeiten sind verwandt**")
    st.plotly_chart(build_acf_chart(report["acf"]), width="stretch", key=f"acf_{rho_pct}_{n}_{seed}")
with col_b:
    naive = cell["naive"]
    factor = 1.96 * naive["rel_std"] / naive["rel_half"]
    st.markdown("**Wie falsch liegt das naive Intervall?**")
    st.metric(f"Zu schmal um den Faktor (ρ = {grid_rho} %, {C.fmt_int(n)} Lkw)", f"{factor:.1f}",
              help="Gemessene Streuung eines Laufs, geteilt durch die mittlere Halbbreite des naiven Intervalls "
                   f"(über {pre['grid_reps']} Läufe, nächste gemessene Auslastung).")
    st.caption(
        f"Direkt benachbarte Lkw haben eine Autokorrelation von {report['acf'][0]:.2f}. Das naive Intervall tut so, als "
        f"hätte der Lauf {C.fmt_int(n)} unabhängige Beobachtungen; tatsächlich trägt er viel weniger Information, "
        f"weil Nachbarn fast dasselbe sagen."
    )

st.markdown("---")
st.subheader("📐 Wie oft trifft das 95-%-Intervall wirklich? Abdeckung")
cov_n = st.select_slider("Lauflänge der Messreihe", options=C.GRID_N, value=n, key="cov_n_select",
                         help="Lkw je Lauf in der vorgerechneten Messreihe.")
st.plotly_chart(build_coverage_chart(pre, int(cov_n)), width="stretch", key=f"coverage_{cov_n}")
cov_cell = coverage_cell(pre, grid_rho, int(cov_n))["variants"]
st.info(
    f"Bei ρ = {grid_rho} % (nächste gemessene Auslastung) und {C.fmt_int(int(cov_n))} Lkw je Lauf enthält das nominale "
    f"95-%-Intervall den wahren Wert beim **naiven Intervall** in {C.fmt_pct(cov_cell['naive']['cover'])} der Fälle, bei "
    f"**Batch Means (20)** in {C.fmt_pct(cov_cell['batch20']['cover'])} und bei **{C.N_REPLICATIONS} Wiederholungen** in "
    f"{C.fmt_pct(cov_cell['repl10']['cover'])}."
)
st.caption(
    f"Je Punkt {pre['grid_reps']} unabhängige Läufe; der Standardfehler einer Abdeckung beträgt dabei höchstens etwa "
    "2.5 Prozentpunkte. Alle Läufe starten leer."
)

st.markdown("---")
st.subheader("🔬 Warm-up: wie viel vom Anfang muss weg?")
st.markdown(
    f"Der leere Start unterschätzt die Schlange. **Welch-Plot:** Mittel über {C.WELCH_REPS} Wiederholungen von je "
    f"{C.fmt_int(C.WELCH_N)} Lkw, geglättet. Am linken Rand sieht man das Einschwingen vom leeren Gate; wie lange es "
    "dauert, hängt von der Auslastung ab (Regler), und bei hoher Auslastung bleibt die Kurve auch nach dem Einschwingen "
    "unruhig."
)
deleted = int(n * warmup_pct / 100)
st.plotly_chart(build_welch_chart(_welch(rho_pct, seed), truth, deleted, report["mser_cut"]), width="stretch",
                key=f"welch_{rho_pct}_{seed}_{deleted}_{report['mser_cut']}")
st.caption(
    f"Senkrecht: der gewählte Abschneidepunkt ({deleted} Lkw) und der automatische MSER-5-Punkt des Hauptlaufs "
    f"({report['mser_cut']} Lkw), soweit sie im gezeigten Bereich liegen."
)
st.markdown("**Welche Warm-up-Regel hilft? Gemessen über viele Läufe (Batch Means mit 20 Batches)**")
st.plotly_chart(build_warmup_chart(pre, grid_rho), width="stretch", key=f"warmup_{grid_rho}")
wu = cell
st.info(
    f"Bei ρ = {grid_rho} % und {C.fmt_int(n)} Lkw liegt der Mittelwert ohne Löschen {wu['none']['bias_pct']:+.1f} % vom "
    f"wahren Wert; nach Löschen der ersten 20 % {wu['del20']['bias_pct']:+.1f} %, mit MSER-5 "
    f"{wu['mser']['bias_pct']:+.1f} %, beim Start im Gleichgewicht {wu['stat']['bias_pct']:+.1f} %. Die Abdeckung "
    f"liegt bei {C.fmt_pct(wu['none']['cover'])} (nichts löschen), {C.fmt_pct(wu['del20']['cover'])} (20 % löschen), "
    f"{C.fmt_pct(wu['mser']['cover'])} (MSER-5) und {C.fmt_pct(wu['stat']['cover'])} (Start im Gleichgewicht)."
)
ws = warmup_summary(pre)
st.success(
    f"**Über alle {ws['total']} gemessenen Zellen** (5 Auslastungen × 6 Lauflängen): MSER-5 liegt in {ws['mser_worse']} "
    f"Zellen mehr als 3 Prozentpunkte **unter** „nichts löschen“ und in {ws['mser_better']} darüber; die ersten 20 % "
    f"zu löschen ändert die Abdeckung in {ws['del20_changed']} Zellen; der Start im Gleichgewicht verbessert sie in "
    f"{ws['stat_better']} Zellen (kurze Läufe bei hoher Auslastung) und verschlechtert sie in {ws['stat_worse']}. "
    f"Das Warm-up ist hier nicht das Hauptproblem, das Intervallverfahren ist es: das naive Intervall kommt in keiner "
    f"Zelle über {C.fmt_pct(ws['naive_max'])}, auch nicht mit Start im Gleichgewicht ({C.fmt_pct(ws['naive_stat_max'])})."
)

st.markdown("---")
st.subheader("🔬 Gemeinsame Zufallszahlen: zwei Systeme fair vergleichen")
speedup = st.select_slider("System B fertigt schneller ab um", options=C.CRN_SPEEDUPS, value=10,
                           format_func=lambda v: f"{v} %", key="crn_speedup",
                           help="System A ist das Gate mit der gewählten Auslastung, System B dasselbe Gate mit "
                                "schnellerer Abfertigung.")
st.markdown(
    "**Wie viel schneller ist B im Mittel?** Das lässt sich mit Läufen schätzen, aber die Differenz zweier verrauschter "
    "Mittel ist doppelt verrauscht, außer beide Systeme sehen **dieselben Ankünfte und (skalierten) Bedienzeiten**."
)
a_path, b_crn, b_ind = _paths(rho_pct, speedup, seed)
st.plotly_chart(build_crn_paths(a_path, b_crn, b_ind, speedup), width="stretch",
                key=f"crn_paths_{rho_pct}_{speedup}_{seed}")
st.caption(
    f"Die ersten {C.PATH_SHOWN} Lkw. Oben laufen die Pfade im Gleichschritt (B wartet nie länger als A, "
    "Lkw für Lkw), unten sind die Zufallszahlen unabhängig und die Pfade haben nichts miteinander zu tun."
)
st.plotly_chart(build_crn_factor_chart(pre), width="stretch", key="crn_factor")
crn_cell = next(c for c in pre["crn"] if c["rho_pct"] == grid_rho and c["speedup_pct"] == speedup)
st.info(
    f"Bei ρ = {grid_rho} % (nächste gemessene Auslastung) und {speedup} % schnellerer Abfertigung streut die geschätzte "
    f"Differenz mit gemeinsamen Zufallszahlen um {crn_cell['sd_crn']:.2f} min, mit unabhängigen um "
    f"{crn_cell['sd_ind']:.2f} min: Varianzfaktor **{crn_cell['variance_factor']:.1f}** (so viel weniger Läufe "
    f"genügen für gleiche Genauigkeit). Wahre Differenz: {crn_cell['truth_diff']:.2f} min "
    f"({pre['crn_reps']} Läufe à {C.fmt_int(pre['crn_n'])} Lkw, beide Systeme im Gleichgewicht gestartet)."
)

st.markdown("---")
st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Es gibt einen Gleichgewichtswert** | Bei zeitveränderlicher Ankunftsrate (Morgenspitze) gibt es keinen stationären Mittelwert; Batch Means und Warm-up schätzen dann nichts Sinnvolles. | **[Zeitvariable Ankünfte](https://sebastianhanisch-time-varying-arrivals-demo.streamlit.app/)** |
| **Der Mittelwert ist die Kennzahl** | Bei seltenen Ereignissen (Überlauf, Verlust) sieht fast kein Lauf das Ereignis, ein Intervall um 0 sagt nichts. | **[Seltene Ereignisse (Splitting)](https://sebastianhanisch-splitting-demo.streamlit.app/)** |
| **Ein Gate mit bekannter Formel** | Hier lässt sich jeder Befund prüfen, und der Start im Gleichgewicht ist möglich. Bei beliebiger Bedienzeit und in Netzen fehlt die Formel meist, dort sind Intervalle die einzige Auskunft. | **[M/G/1, Kingman-Näherung](https://sebastianhanisch-mg1-kingman-demo.streamlit.app/)** und **[Jackson-Netze](https://sebastianhanisch-jackson-network-demo.streamlit.app/)** |
| **Batches länger als die „Erinnerung“ des Systems** | Bei hoher Auslastung ist die Erinnerung lang: viele kurze Batches sind noch verwandt, die Intervalle zu schmal (die Abdeckung sinkt mit der Batch-Zahl, Abbildung oben). | kein Folgestück; Verfahren mit automatischer Batch-Länge und Abbruch bei Zielgenauigkeit nicht umgesetzt |
| **Gemeinsame Zufallszahlen helfen** | Der Gewinn hängt stark von der Auslastung ab (Abbildung oben) und setzt voraus, dass beide Systeme dieselben Zufallsereignisse sehen. | kein Folgestück |
"""
)
st.caption(
    "Verwandt im Portfolio: [markov-queue-demo](https://sebastianhanisch-markov-queue-demo.streamlit.app/) (Zusatzstück: die Einschwingzeit, die hier aus Läufen geschätzt wird, ergibt sich dort exakt aus der Kette), [mm1-queue-demo](https://sebastianhanisch-mm1-queue-demo.streamlit.app/) (Stück 1: Streuung eines "
    "Laufs und Startverzerrung), [forecast-interval-demo](https://sebastianhanisch-forecast-interval-demo.streamlit.app/) "
    "(prüft ebenfalls, ob Intervalle ihre Nennabdeckung halten, dort für Prognosen)."
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Ziel:** Schätze $\theta = E[W_q]$, die mittlere Wartezeit im Gleichgewicht ($\theta = \rho/(\mu - \lambda)$ bei M/M/1),
aus einem Lauf $W_1, \dots, W_n$. Ein **zweiseitiges 95-%-Intervall** $\bar W \pm h$ hat die **Abdeckung**
$P(\theta \in \bar W \pm h)$; gemessen wird der Anteil der Läufe, in denen der wahre Wert enthalten ist.

**Naives Intervall.** $h = t_{n-1}\,s/\sqrt n$ setzt unabhängige Werte voraus. Bei Autokorrelation $r_k$ ist
$\mathrm{Var}(\bar W) \approx \frac{\sigma^2}{n}\bigl(1 + 2\sum_{k\ge 1}r_k\bigr)$, bei Wartezeiten mit
$r_k$ nahe 1 ein Vielfaches des naiven Werts.

**Batch Means.** Teile den Lauf in $b$ Blöcke der Länge $m = \lfloor n/b \rfloor$ (Rest am Ende verworfen); die
Blockmittel $\bar W_1,\dots,\bar W_b$ sind für großes $m$ fast unabhängig und fast normalverteilt:
$h = t_{b-1}\,s_b/\sqrt b$ mit der Standardabweichung $s_b$ der Blockmittel.

**Unabhängige Wiederholungen.** $R$ Läufe mit eigenen Zufallsströmen, Mittel $\bar W_1,\dots,\bar W_R$:
$h = t_{R-1}\,s_R/\sqrt R$. Unabhängig, aber jede Wiederholung startet leer.

**Warm-up.** Der Start im leeren Gate verzerrt $E[W_k]$ für kleine $k$ nach unten. **MSER-5** (White 1997): bilde
Blockmittel $y_j$ der Länge 5 und wähle den Abschneidepunkt $d$, der
$\sum_{j>d}(y_j-\bar y_d)^2/(m-d)^2$ minimiert. **Welch:** Mittel über Wiederholungen je Kundennummer, gleitend
geglättet. **Start im Gleichgewicht:** $W_1 = 0$ mit Wahrscheinlichkeit $1-\rho$, sonst exponentiell mit Rate
$\mu - \lambda$ (nur möglich, weil die Formel bekannt ist).

**Gemeinsame Zufallszahlen.** Für zwei Systeme $A, B$ gilt $\mathrm{Var}(\bar W_A - \bar W_B) = \mathrm{Var}\bar W_A +
\mathrm{Var}\bar W_B - 2\,\mathrm{Cov}(\bar W_A,\bar W_B)$; gleiche Ankünfte und gleiche (skalierte) Bedienzeiten machen
die Kovarianz positiv. Der **Varianzfaktor** ist $\mathrm{Var}_{\text{unabhängig}}/\mathrm{Var}_{\text{gemeinsam}}$.

**Erzeugung.** Wartezeiten per Lindley-Rekursion $W_{k+1} = \max(0, W_k + S_k - A_{k+1})$ aus einem
Ganzzahl-Zufallsgenerator (SplitMix64), Ankünfte und Bedienzeiten mit getrennten Strömen; in mm1-queue-demo ist gezeigt,
dass sie Kunde für Kunde dieselben Wartezeiten liefert wie die Ereignissimulation.

Implementiert in `oa_estimators.py` (Intervalle, Batch Means, MSER-5, Welch, Autokorrelation),
`oa_simulation.py` (Generator, Lindley-Rekursion), `oa_evaluation.py` (Abdeckungs- und Vergleichsstudien),
`generate_precomputed.py` (vorgerechnete Messreihen).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html))."
)
