"""BER/FER of complete chains compared to the AFF3CT references (lib/aff3ct/refs, Plan.md phase 2).

Each point is simulated with fewer frame errors than the reference: the measured FER must be within 4 standard
deviations (binomial, measure and reference combined) of the reference one. Skipped when the ``refs`` submodule of
AFF3CT is not checked out (``git -C lib/aff3ct submodule update --init refs``).
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import numpy as np
import pytest
import streampu as spu

import aff3ct as af

REFS = Path(__file__).resolve().parent.parent / "lib" / "aff3ct" / "refs"
sys.path.insert(0, str(REFS.parent.parent.parent / "examples"))

pytestmark = pytest.mark.skipif(not REFS.is_dir() or not any(REFS.iterdir()), reason="lib/aff3ct/refs not checked out")


def read_ref(path: Path) -> dict[float, tuple[int, int, float]]:
    """{Eb/N0: (FRA, FE, FER)} of a reference file."""
    pts = {}
    for line in path.read_text().splitlines():
        cols = [c.strip() for c in re.split(r"\|\|?", line)]
        if len(cols) >= 7 and re.fullmatch(r"-?[0-9.]+", cols[1] or "x") and re.fullmatch(r"[0-9]+", cols[2] or "x"):
            pts[float(cols[1])] = (int(cols[2]), int(cols[4]), float(cols[6]))
    return pts


def check(measured: list[tuple[float, float, float, int]], ref: dict, ebn0s):
    for ebn0, _ber, fer, fra in measured:
        r_fra, _r_fe, r_fer = ref[ebn0]
        sd = math.sqrt(r_fer * (1 - r_fer) / r_fra + fer * (1 - fer) / fra)
        assert abs(fer - r_fer) <= 4 * sd + 1e-3, (ebn0, fer, r_fer, sd)


def run(K, N, enc, dec, ebn0s, max_fe, adapt=None):
    """Single-threaded BFER chain src -> enc -> BPSK -> AWGN -> dec -> monitor."""
    src = af.src.source(K, type="RAND", seed=0)
    mdm = af.mdm.modem(N, type="BPSK")
    chn = af.chn.channel(N, type="AWGN", seed=1)
    mnt = af.mnt.bfer(K, n_frame_errors=max_fe)
    sigma = spu.array([1.0], dtype=spu.float32)
    u = src.generate()[0]
    dec.decode_siho(mdm.demodulate(sigma, chn.add_noise(sigma, mdm.modulate(enc.encode(u)))))
    mnt.check_errors(u, dec["decode_siho::V_K"])
    seq = spu.Sequence(mnt["check_errors::status"])
    out = []
    for ebn0 in ebn0s:
        s = af.tools.sigma_from_ebn0(ebn0, K / N)
        sigma.numpy[...] = s.sigma
        if adapt:
            adapt(s)
        mnt.reset()
        seq.exec()
        out.append((ebn0, mnt.ber, mnt.fer, mnt.n_analyzed_frames))
    return out


def test_polar_sc_matches_the_reference():
    from polar_bfer import simulate

    ref = read_ref(REFS / "POLAR/AWGN/BPSK/SC/Polar_N128_K96_SC_NO_SYS_p32.txt")
    ebn0s = [1.0, 2.0, 3.0]
    check(simulate(96, 128, ebn0s, max_fe=300, n_threads=1, quiet=True), ref, ebn0s)


def test_bch_matches_the_reference():
    ref = read_ref(REFS / "BCH/AWGN/BPSK/ALGEBRAIC/BCH_N127_K106_algebraic_T3.txt")
    GF = af.tools.BCH_polynomial_generator(127, 3)
    K, N = 127 - GF.n_rdncy, 127
    assert K == 106
    enc, dec = af.enc.bch(K, N, GF), af.dec.bch(K, N, GF)
    ebn0s = [4.0, 5.0, 6.0]
    check(run(K, N, enc, dec, ebn0s, max_fe=300), ref, ebn0s)


def test_ldpc_bp_matches_the_reference(tmp_path):
    # (128, 64) CCSDS code; the reference source is all-zero (AZCW): same statistics for a linear code
    path = REFS / "LDPC/AWGN/BPSK/BP_HORIZONTAL_LAYERED/SPA/LDPC_N128_K64_hlayered_SPA_i50_CCSDS.txt"
    conf = REFS.parent / "conf" / "dec" / "LDPC" / "CCSDS_64_128.alist"
    if not conf.exists():
        pytest.skip("lib/aff3ct/conf not checked out (CCSDS_64_128.alist)")
    ref = read_ref(path)
    H = af.tools.AList.read(conf)
    af.tools.AList.write(H, tmp_path / "H.alist")
    assert af.tools.AList.read(tmp_path / "H.alist") == H
    N, K = max(H.shape), max(H.shape) - min(H.shape)
    # as the AFF3CT simulator: G computed by the encoder from H, its information bits given to the decoder
    enc = af.enc.ldpc(K, N, af.tools.Sparse_matrix(), H, type="LDPC_H")
    dec = af.dec.ldpc(K, N, H, enc.info_bits_pos, type="BP_HORIZONTAL_LAYERED", implem="SPA", n_ite=50)
    G, info_bits_pos = af.tools.LDPC_matrix_handler.transform_H_to_G(H, "LU_DEC")
    assert G.n_connections > 0 and len(info_bits_pos) == K
    ebn0s = [2.0, 3.0]
    check(run(K, N, enc, dec, ebn0s, max_fe=200), ref, ebn0s)


def test_polar_sc_multithreaded_matches_the_reference():
    # Monitor_BFER_AR: the 4 threads stop on the total number of frame errors (no bias of the reduced FER)
    from polar_bfer import simulate

    ref = read_ref(REFS / "POLAR/AWGN/BPSK/SC/Polar_N128_K96_SC_NO_SYS_p32.txt")
    ebn0s = [1.0, 2.0, 3.0]
    res = simulate(96, 128, ebn0s, max_fe=300, n_threads=4, quiet=True)
    check(res, ref, ebn0s)
