# Output Analysis – wie viel Vertrauen verdient eine Simulation? (Streamlit-Demo)

Interaktive Demo zur **Auswertung von Simulationsläufen** am M/M/1-Gate aus
[mm1-queue-demo](https://github.com/sebastian-hanisch/mm1-queue-demo). **Zweites Stück der Konzepte-Linie
„Warteschlangentheorie und Simulation“** im Portfolio von [Sebastian Hanisch](https://sebastianhanisch.net)
(Operations Research und Machine Learning): ein Verfahren, ein wachsendes Beispiel, jedes Folgestück hebt genau eine
Annahme auf.

Stück 1 zeigte, dass ein einzelner Simulationslauf um die Formel streut. Hier die Folgefrage: **Wie gibt man diese
Unsicherheit ehrlich an?** Weil der wahre Wert der M/M/1-Schlange aus der Formel bekannt ist, kann die Demo messen, **ob
ein nominales 95-%-Intervall sein Versprechen hält**, für das naive Intervall, für Batch Means und für unabhängige
Wiederholungen, dazu für Warm-up-Regeln (was vom leeren Start muss weg?) und für gemeinsame Zufallszahlen beim Vergleich
zweier Systeme.

## Kernfrage

Wie oft enthält ein 95-%-Intervall den wahren Wert wirklich, und was entscheidet darüber: das Intervallverfahren, die
Lauflänge, die Auslastung, das Warm-up?

## Modell und Methodik

- **Ausgabeprozess:** die Wartezeiten aufeinanderfolgender Lkw einer M/M/1-Schlange (3 min mittlere Abfertigung, Auslastung
  10–97 %). Sie entstehen per Lindley-Rekursion W′ = max(0, W + S − A) aus einem Ganzzahl-Zufallsgenerator (SplitMix64) mit
  **getrennten Strömen** für Ankünfte und Bedienzeiten. In mm1-queue-demo ist gezeigt, dass sie Kunde für Kunde dieselben
  Wartezeiten liefert wie die Ereignissimulation; hier dient sie als schneller Erzeuger.
- **Intervalle** (`oa_estimators.py`, je Regel eine Funktion): naiv (s/√n), Batch Means (5/10/20/30 Batches),
  unabhängige Wiederholungen (10 × n/10 Lkw); t-Quantile aus einer Tabelle (scipy nur als Testreferenz).
- **Warm-up:** die ersten 10/20/50 % löschen, MSER-5 (White 1997), Welch-Plot, Start im Gleichgewicht (nur möglich, weil die
  Formel die stationäre Verteilung der ersten Wartezeit liefert).
- **Gemeinsame Zufallszahlen:** System B fertigt um 5/10/20/50 % schneller ab, mit denselben Ankünften und denselben
  (skalierten) Bedienzeiten wie System A, gegen unabhängige Läufe.
- **Vorgerechnete Messreihen** (`generate_precomputed.py` → `precomputed_sweep.json`, knapp fünf Minuten parallel):
  5 Auslastungen × 6 Lauflängen je 400 Läufe für alle Methoden und Warm-up-Strategien, dazu 5 Auslastungen × 4
  Beschleunigungen je 400 Läufe für die gemeinsamen Zufallszahlen. Live läuft nur der gewählte Einzellauf, der Welch-Plot
  (50 Wiederholungen) und das Pfadpaar der gemeinsamen Zufallszahlen.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py`; die Messreihen haben 400 Läufe je Zelle, der Standardfehler einer
Abdeckung beträgt dabei höchstens 2.5 Prozentpunkte.

| Frage | Befund |
|---|---|
| Trifft das naive 95-%-Intervall? | **Nein, in keiner der 30 Zellen** (5 Auslastungen × 6 Lauflängen) häufiger als in 51 % der Fälle, auch nicht mit Start im Gleichgewicht (höchstens 53 %). Bei 10 000 Lkw: ρ = 50 % **49 %**, 70 % 28 %, 80 % 18 %, 90 % **9 %**, 95 % **4 %**. Längere Läufe helfen nicht (ρ = 90 %: 12 % bei 1 000, 9 % bei 50 000 Lkw). |
| Warum nicht? | Nachbarn in der Reihe sind fast gleich: Autokorrelation der Wartezeiten bei ρ = 90 % rund 0.99. Das naive Intervall ist bei 10 000 Lkw um den Faktor **3** (ρ = 50 %), **18** (ρ = 90 %) bzw. **36** (ρ = 95 %) zu schmal. |
| Wie gut ist Batch Means? | Bei 10 000 Lkw und 20 Batches: ρ = 50 % **93 %**, 70 % 94 %, 80 % 91 %, 90 % **86 %**, 95 % **65 %**. Bei 50 000 Lkw und ρ = 95 % erst 85 %: der nominale Wert wird auch dort nicht erreicht. |
| Wie viele Batches? | **Weniger, längere Batches sind hier besser.** Bei ρ = 95 % sinkt die Abdeckung mit der Batch-Zahl (10 000 Lkw: 82 % bei 5, 78 % bei 10, 65 % bei 20, 60 % bei 30 Batches). Bei nur 1 000 Lkw und ρ = 90 %: 74 % mit 5 gegen 55 % mit 20 Batches. |
| Wiederholungen statt eines langen Laufs? | Unabhängig, aber jede startet leer: bei ρ = 95 % und 1 000 Lkw (10 × 100) liegt der Mittelwert etwa **70 %** unter dem wahren Wert. Bei ρ ≤ 80 % und 10 000 Lkw treffen sie wie Batch Means (91–92 %). |
| Wie groß ist die Startverzerrung? | Nur bei kurzen Läufen und hoher Auslastung: ρ = 95 %, 1 000 Lkw: Mittelwert ohne Löschen etwa **−32 %**, mit Start im Gleichgewicht etwa +1 %. Bei 10 000 Lkw und ρ ≤ 90 % liegt sie im Rauschen. |
| Hilft Anfang löschen? | Kaum: die ersten 20 % zu löschen ändert die Abdeckung in keiner der 30 Zellen um mehr als 3 Prozentpunkte. Der Start im Gleichgewicht hilft in 4 Zellen (kurze Läufe bei hoher Auslastung) und schadet in keiner. |
| Und MSER-5? | **Es verschlechtert die Abdeckung**: in 23 von 30 Zellen mehr als 3 Punkte unter „nichts löschen“, in keiner darüber; der Mittelwert liegt in 25 Zellen mehr als 1 % unter dem wahren Wert (ρ = 90 %, 10 000 Lkw: etwa −7 %, ρ = 95 %: etwa −12 %). |
| Gemeinsame Zufallszahlen? | Der Gewinn hängt an der Auslastung **und** an der Größe des Unterschieds. System B 5 % schneller: Varianzfaktor **63** (ρ = 50 %), 21 (70 %), 9.7 (80 %), 3.5 (90 %), 1.7 (95 %). Bei 50 % schneller nur noch 1.9 (ρ = 50 %) bis 1.0 (ρ = 90 %). Die geschätzte Differenz bleibt unverzerrt. |

## Befunde und Korrekturen gegenüber dem Plan

- **Die Vorab-Messreihe war eine Skizze und ist übertroffen:** 400 Läufe bei 10 000 Lkw in drei Auslastungen. Alle
  Richtungen bestätigten sich; die Zahlen sind jetzt über 30 Zellen gemessen. Das naive Intervall: 51 / 8 / 4 % vorab gegen
  49 / 9 / 4 % in der endgültigen Messreihe.
- **MSER-5 war im Plan als „prüfen“ vermerkt**, weil es vorab nach unten verzerrte. Die Implementierung ist an einer Reihe
  mit künstlichem Einschwingen von Hand geprüft (schneidet exakt am Ende des Einschwingens ab, auf einer konstanten Reihe
  nichts); der negative Befund steht trotzdem so da. Eine Erklärung habe ich nicht untersucht; naheliegend ist, dass das
  Verfahren bei langem „Gedächtnis“ eine ruhige Phase fürs Gleichgewicht hält und damit nach unten verzerrt. Andere
  Blockgrößen oder Abschneidegrenzen könnten anders ausfallen.
- **Gemeinsame Zufallszahlen: „wirkt nur bei niedriger Auslastung“ war zu grob.** Der Faktor hängt stark auch von der Größe
  des Unterschieds ab (5 % gegen 50 % schneller: 63 gegen 1.9 bei ρ = 50 %).
- **Zeile „Batch-Mittel sind normalverteilt“ in der Grenzentabelle ersetzt:** Die Daten zeigen kein Normalverteilungs-
  Problem, sondern zu kurze Batches bei hoher Auslastung (Abdeckung fällt mit der Batch-Zahl). Schmeiser (1982) empfiehlt
  10 bis 30 Batches unter der Annahme unabhängiger, normalverteilter Batch-Mittel; diese Annahme ist hier bei hoher
  Auslastung nicht erfüllt.
- **Die Simulation ist eine Lindley-Rekursion, keine Ereignisliste.** Der Linienplan nennt Stück 2 „ereignisdiskrete
  Simulation“; für den Ausgabeprozess (Wartezeit je Kunde) liefern beide dieselben Zahlen (belegt in mm1-queue-demo).
- **Der Welch-Plot bleibt auch mit 50 Wiederholungen unruhig** (bei hoher Auslastung ist das Einschwingen kurz gegenüber dem
  Rauschen); er zeigt das Einschwingen am linken Rand, taugt hier aber nicht als präzises Werkzeug.

## Ehrliche Grenzen

- Der wahre Wert ist bekannt (Formel); in echten Systemen fehlt er, dort sind Intervalle die einzige Auskunft, und der
  Start im Gleichgewicht ist nicht möglich.
- Gemessen wird nur die mittlere Wartezeit eines FIFO-Systems mit einem Server und exponentiellen Zeiten, bei Auslastungen
  bis 97 % (Gleichgewichtsfälle).
- Die Messreihen haben 400 Läufe je Zelle; einzelne Abdeckungen sind auf etwa ±2.5 Prozentpunkte genau, die Unterschiede
  unter 3 Punkten sind Rauschen.
- Die Zahl der Batches ist auf höchstens 30 begrenzt (die t-Tabelle ist bis 30 Freiheitsgrade genau, darüber leicht
  konservativ); die Zahl der Wiederholungen ist fest 10.
- Die gemeinsamen Zufallszahlen koppeln Ankünfte und (skalierte) Bedienzeiten; beide Systeme starten im Gleichgewicht,
  die Messung ist also frei von Startverzerrung. Andere Kopplungen oder Systeme mit verschiedener Struktur sind nicht untersucht.
- Die Live-Ansicht rechnet **einen** Lauf; was ein einzelnes Intervall trifft, ist ein Münzwurf, die Abdeckung steht in den
  vorgerechneten Messreihen.

## Verwandte Demos im Portfolio

- [`mm1-queue-demo`](https://github.com/sebastian-hanisch/mm1-queue-demo): Stück 1 der Linie, Streuung eines Laufs und
  Startverzerrung, aus denen diese Demo die Frage nach dem Intervall gewinnt.
- [`forecast-interval-demo`](https://github.com/sebastian-hanisch/forecast-interval-demo): prüft ebenfalls, ob
  Intervalle ihre Nennabdeckung halten, dort für Prognosen (konforme Kalibrierung, Wochentage, Verteilungswechsel).

## Bewusst nicht umgesetzt

Jede dieser Annahmen hebt ein Folgestück der Linie auf:

| Annahme | Folgestück |
|---|---|
| Es gibt einen Gleichgewichtswert | Zeitvariable Ankünfte |
| Der Mittelwert ist die Kennzahl | Seltene Ereignisse (Splitting) |
| Ein Gate mit bekannter Formel | M/G/1 (Kingman-Näherung), Jackson-Netze |

Kein Folgestück: Bootstrap-Intervalle, Verfahren mit automatischer Batch-Länge oder Abbruch bei Zielgenauigkeit,
andere Kopplungen für gemeinsame Zufallszahlen.

## Tests

134 Tests, rund 15 s: t-Quantile gegen scipy, Intervalle, Batch-Mittel, MSER-5 (künstliches Einschwingen, konstante Reihe,
Handrechnung), Welch-Mittelung und Autokorrelation von Hand, Generator gegen die Referenzfolge, Lindley-Rekursion an einer
Drei-Lkw-Instanz, stationärer Start, Gleichlauf der Ströme bei gemeinsamen Zufallszahlen (das schnellere System wartet nie
länger, Lkw für Lkw), kleine Abdeckungsstudien, Vollständigkeit der vorgerechneten Datei, Presets/Permalink,
AppTest-Rauchtests (Standard, jedes Preset, Randwerte, Permalink-Grenzen, Würfel-Knopf) und `test_claims.py` für jede Zahl
dieser README.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche |
| `oa_formulas.py` | wahrer Wert (Wq der M/M/1-Schlange) |
| `oa_simulation.py` | Generator, Lindley-Rekursion, stationärer Start, getrennte Ströme |
| `oa_estimators.py` | Intervalle, Batch Means, MSER-5, Welch, Autokorrelation |
| `oa_evaluation.py` | Berichte, Abdeckungs- und Vergleichsstudien |
| `generate_precomputed.py` | rechnet die Messreihen vor → `precomputed_sweep.json` |
| `oa_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `oa_presets.py`, `oa_constants.py` | Presets, Permalink, Grenzen |
| `tests/` | siehe oben |

## Literatur

- White, K. P. Jr. (1997): An effective truncation heuristic for bias reduction in simulation output. *Simulation* 69(6),
  323–334 (MSER).
- Schmeiser, B. (1982): Batch size effects in the analysis of simulation output. *Operations Research* 30(3), 556–568.

## Lokal ausführen

```
pip install -r requirements.txt
streamlit run app.py
```

Tests: `pip install -r requirements-dev.txt` und `python -m pytest tests/ -v`. Messreihen neu rechnen:
`python generate_precomputed.py`.

Gebaut mit Streamlit und Plotly.
