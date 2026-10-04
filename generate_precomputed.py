"""Rechnet die teuren Messreihen vor (Build-Zeit, nicht in der App): `python generate_precomputed.py [Prozesse]`
schreibt `precomputed_sweep.json`.

  coverage  Auslastung × Lauflänge: Abdeckung, Verzerrung, Streuung, Breite je Methode und Warm-up-Strategie
  crn       Auslastung × Beschleunigung: Streuung der Differenz mit und ohne gemeinsame Zufallszahlen"""

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import oa_constants as C
from oa_evaluation import PRECOMPUTED_PATH, coverage_study, crn_study


def _coverage_task(args):
    rho, n_idx, n = args
    return coverage_study(rho, n, C.GRID_REPS, seed_base=rho * 10_000_000 + n_idx * 1_000_000)


def _crn_task(args):
    rho, sp = args
    return crn_study(rho, sp, C.CRN_N, C.CRN_REPS, seed_base=rho * 10_000_000 + sp * 100_000 + 50_000_000)


def main(workers):
    t0 = time.time()
    cov_jobs = [(r, i, n) for r in C.GRID_RHO_PCT for i, n in enumerate(C.GRID_N)]
    crn_jobs = [(r, sp) for r in C.GRID_RHO_PCT for sp in C.CRN_SPEEDUPS]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        coverage = list(ex.map(_coverage_task, sorted(cov_jobs, key=lambda j: -j[2])))
        crn = list(ex.map(_crn_task, crn_jobs))
    coverage.sort(key=lambda c: (c["rho_pct"], c["n"]))
    out = {"grid_reps": C.GRID_REPS, "crn_reps": C.CRN_REPS, "crn_n": C.CRN_N, "coverage": coverage, "crn": crn}
    Path(PRECOMPUTED_PATH).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"fertig in {time.time() - t0:.0f} s -> {PRECOMPUTED_PATH}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else min(6, os.cpu_count() or 1))
