#!/usr/bin/env python3
"""Figures of the documentation (docs/assets/figures/*.svg), computed by the examples (examples/*.py).

Run before ``mkdocs build`` (the CI does it in the docs jobs); the figures are not versioned.

    python scripts/doc_figures.py [--threads 4] [--quick]
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "assets" / "figures"
sys.path.insert(0, str(ROOT / "examples"))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--threads", type=int, default=4)
    p.add_argument("--quick", action="store_true", help="fewer frame errors (draft figures)")
    a = p.parse_args()
    max_fe = 30 if a.quick else 200
    OUT.mkdir(parents=True, exist_ok=True)

    import codecs_comparison
    import mutual_information
    import fixed_point
    import modulations
    import polar_bfer
    import turbo_lte

    def step(name, f):
        t = time.time()
        f()
        print(f"{name}: {time.time() - t:.1f} s", flush=True)

    def polar():
        res = polar_bfer.simulate(ebn0s=[0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0], max_fe=max_fe,
                                  n_threads=a.threads, quiet=True)
        polar_bfer.plot(res, OUT / "polar_bfer.svg")

    def codecs():
        ebn0s = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
        res = codecs_comparison.run(ebn0s, max_fe=max_fe, n_threads=a.threads, max_frames=100_000)
        codecs_comparison.plot(res, ebn0s, OUT / "codecs_comparison.svg")

    def modems():
        ebn0s = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0]
        modulations.plot(modulations.run(ebn0s, n_frames=100 if a.quick else 1000), ebn0s, OUT / "modulations_ber.svg")
        modulations.plot_constellation(OUT / "qam16.svg")

    def fixed():
        ebn0s = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        fixed_point.plot(fixed_point.run(ebn0s, max_fe=max_fe, n_threads=a.threads), ebn0s, OUT / "fixed_point.svg")

    def turbo():
        ebn0s = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]
        cdc, crc = turbo_lte.codec_from_keywords()
        turbo_lte.plot(turbo_lte.simulate(cdc, crc, ebn0s, max_fe, a.threads), ebn0s, OUT / "turbo_lte.svg")

    def capacity():
        esn0s = [-10.0, -7.5, -5.0, -2.5, 0.0, 2.5, 5.0]
        mutual_information.plot(esn0s, mutual_information.measure(esn0s, n_frames=20 if a.quick else 100,
                                                                   n_threads=a.threads), OUT / "capacity.svg")

    for name, f in [("polar", polar), ("codecs", codecs), ("modems", modems), ("fixed point", fixed),
                    ("turbo", turbo), ("capacity", capacity)]:
        step(name, f)


if __name__ == "__main__":
    main()
