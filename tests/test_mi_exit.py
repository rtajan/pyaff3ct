"""Mutual information and EXIT monitors, their reporters, af.mnt.reduce."""

import sys
from pathlib import Path

import numpy as np
import pytest
import streampu as spu

import aff3ct as af

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "examples"))


def J(sigma, n=400_000):
    """Mutual information of Gaussian LLRs of mean sigma^2 / 2 and variance sigma^2 (Monte Carlo)."""
    r = np.random.default_rng(0).normal(sigma**2 / 2, sigma, n)
    return 1 - np.mean(np.logaddexp(0, -r)) / np.log(2)


def test_mutual_information_is_the_bi_awgn_capacity():
    import mutual_information as ex  # examples/

    esn0s = [-5.0, 0.0, 5.0]
    for m, t in zip(ex.measure(esn0s, N=16384, n_frames=20, n_threads=2), ex.theory(esn0s)):
        assert m == pytest.approx(t, abs=0.005)


def test_exit_monitor_with_gaussian_llrs():
    N = 8192
    mnt = af.mnt.exit(N, n_trials=10)
    assert isinstance(mnt, af.mnt.Monitor_EXIT) and mnt.max_n_trials == 10
    rng = np.random.default_rng(1)
    bits = rng.integers(0, 2, N)
    s_a, s_e = 1.0, 3.0
    llr = [(1 - 2 * bits) * s**2 / 2 + rng.normal(0, s, N) for s in (s_a, s_e)]  # positive for a bit 0
    mnt.check_mutual_info(spu.array(bits.tolist(), dtype=spu.int32),
                          *(spu.array(x.astype(np.float32), dtype=spu.float32) for x in llr))
    assert mnt.n_trials == 1
    assert mnt.I_A == pytest.approx(J(s_a), abs=0.01) and mnt.I_E == pytest.approx(J(s_e), abs=0.01)


def test_reduce_sums_the_threads():
    K = 64
    for mnt, n_threads in [(af.mnt.bfer(K, n_frame_errors=50), 3), (af.mnt.Monitor_BFER_AR(K, 50), 3)]:
        src, mdm, chn = af.src.source(K, type="RAND"), af.mdm.modem(K, type="BPSK"), af.chn.channel(K, type="AWGN")
        dec = af.codec.uncoded(K, K).decoder_siho  # one chain per monitor (a sequence runs every bound task)
        s = spu.array([1.0], dtype=spu.float32)
        u = src.generate()[0]
        mnt.check_errors(u, dec.decode_siho(mdm.demodulate(s, chn.add_noise(s, mdm.modulate(u))))[1])
        seq = spu.Sequence(mnt["check_errors::status"], n_threads=n_threads)
        af.tools.seed_sequence(seq)
        seq.exec()
        total = af.mnt.reduce(seq, mnt)
        clones = seq.get_cloned_modules(mnt)
        if hasattr(mnt, "is_shared_with"):  # Monitor_BFER_AR: already the totals
            assert total is mnt and mnt.n_fe >= 50
        else:
            assert total.n_fe == sum(c.n_fe for c in clones) and total.n_analyzed_frames == sum(
                c.n_analyzed_frames for c in clones)
            assert total is not mnt and type(total) is type(mnt)


def test_reporters():
    N = 128
    mi = af.mnt.mi(N, n_trials=5)
    ex = af.mnt.exit(N, n_trials=5)
    assert isinstance(af.tools.Reporter_MI(mi), spu.Reporter)
    assert isinstance(af.tools.Reporter_EXIT(ex, af.tools.Sigma(1.0)), spu.Reporter)
