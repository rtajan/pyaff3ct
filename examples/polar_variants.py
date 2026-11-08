#!/usr/bin/env python3
"""Variants of the polar codes: multi-kernel, PAC (polarization-adjusted convolutional) and pre-transformed polar
codes (docs/guides/polar.md). The kernels, frozen bits and pre-transforms are read from the AFF3CT configuration
files (lib/aff3ct/conf, fetched by scripts/fetch_aff3ct_data.sh).

    python examples/polar_variants.py
"""

from __future__ import annotations

from pathlib import Path

import aff3ct as af
from codecs_comparison import simulate

CDE = Path(__file__).resolve().parent.parent / "lib" / "aff3ct" / "conf" / "cde" / "awgn_polar_codes"


def available() -> bool:
    return (CDE / "MK" / "3_2_2_2_3" / "N72.cde").exists() and (CDE / "PT" / "7" / "N128_K64_PT.txt").exists()


def codecs() -> dict:
    out = {}
    # --8<-- [start:mk]
    # multi-kernel polar code of 72 bits: 3 x 2 x 2 x 2 x 3 kernels (the code file gives the kernels and their order)
    out["Polar MK (72, 36), SCL L=8"] = af.codec.polar_mk(
        36, 72, pc_code_path=str(CDE / "MK" / "3_2_2_2_3" / "N72.cde"), fbg_type="GA",
        dec_type="SCL", dec_implem="NAIVE", dec_L=8)
    # --8<-- [end:mk]
    # --8<-- [start:pac]
    # PAC code: a convolutional pre-transform (octal polynomial 0o33) before the polar transform, Reed-Muller rule
    out["PAC (128, 64), SCL L=8"] = af.codec.polar_pac(
        64, 128, enc_conv="0o33", fbg_type="RM", dec_type="SCL", dec_implem="NAIVE", dec_L=8)
    # --8<-- [end:pac]
    # --8<-- [start:pt]
    # pre-transformed polar code: frozen bits and pre-transform matrix read from files
    out["Polar PT (128, 64), SCL L=8"] = af.codec.polar_pt(
        64, 128, fbg_type="FILE", fbg_path_fb=str(CDE / "PT" / "7" / "N128_K64_RP.txt"),
        ptg_type="FILE", ptg_path_fb=str(CDE / "PT" / "7" / "N128_K64_PT.txt"), dec_implem="NAIVE", dec_L=8)
    # --8<-- [end:pt]
    return out


def run(ebn0s=(1.0, 2.0), max_fe: int = 100, n_threads: int = 2) -> dict[str, list[float]]:
    return {name: simulate(cdc, None, ebn0s, max_fe, n_threads) for name, cdc in codecs().items()}


if __name__ == "__main__":
    if not available():
        raise SystemExit("configuration files missing: scripts/fetch_aff3ct_data.sh")
    for name, fer in run().items():
        print(f"{name:30s}", "  ".join(f"{f:.2e}" for f in fer))
