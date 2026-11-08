"""The examples of the documentation (examples/*.py, included in docs/ by snippets) run and give the right results."""

from __future__ import annotations

import io
import math
import sys
from contextlib import redirect_stdout
from pathlib import Path

import numpy as np
import pytest

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
sys.path.insert(0, str(EXAMPLES))

import _references as refs  # noqa: E402


def quiet(f, *args, **kwargs):
    with redirect_stdout(io.StringIO()) as out:
        res = f(*args, **kwargs)
    return res, out.getvalue()


def near_reference(name: str, ebn0: float, fer: float, frames: int, n_sd: float = 4.0):
    """FER within n_sd binomial standard deviations (measure and reference) of the reference."""
    if not refs.available():
        return
    r = refs.read(name)
    i = r["ebn0"].index(ebn0)
    p, n = r["fer"][i], r["fra"][i]
    sd = math.sqrt(p * (1 - p) / n + fer * (1 - fer) / frames)
    assert abs(fer - p) <= n_sd * sd + 1e-3, (name, ebn0, fer, p)


def test_first_chain():
    import first_chain

    res, out = quiet(first_chain.run, ebn0=2.0, max_fe=100)
    f = res["first_frame"]
    assert f["u"].shape == (1, 96) and f["v"].shape == (1, 96) and f["llr"].shape == (1, 128)
    assert f["n_be"] == int((f["u"] != f["v"]).sum())
    assert "FER =" in out and res["n_fe"] >= 100
    near_reference("POLAR/AWGN/BPSK/SC/Polar_N128_K96_SC_SYS_p32.txt", 2.0, res["fer"], res["frames"])


def test_polar_bfer():
    import polar_bfer

    res = polar_bfer.simulate(ebn0s=[1.0, 2.0], max_fe=100, n_threads=2)  # the terminal writes to std::cout
    for ebn0, _ber, fer, frames in res:
        near_reference("POLAR/AWGN/BPSK/SC/Polar_N128_K96_SC_NO_SYS_p32.txt", ebn0, fer, frames)


def test_codecs_comparison():
    import codecs_comparison

    res = codecs_comparison.run(ebn0s=[1.0, 3.0], max_fe=50, n_threads=2)
    assert {"Polar SC", "Polar CA-SCL (L=8)", "RSC (BCJR)", "Turbo LTE (6 it.)", "Repetition"} <= set(res)
    for label, fer in res.items():
        assert fer[0] > fer[1] or math.isnan(fer[1]), label  # better at 3 dB than at 1 dB
    assert res["Polar CA-SCL (L=8)"][1] < res["Polar SC"][1] < res["Repetition"][1]


def near_theory(ber, expected, n_bits, model=0.0, n_sd=4):
    """BER measured on n_bits bits close to its expected value: n_sd standard deviations of the estimate (binomial
    count of errors), plus the relative error of the model (approximate formula)."""
    sd = math.sqrt(expected * (1 - expected) / n_bits)
    return abs(ber - expected) <= n_sd * sd + model * expected


def test_modulations():
    import modulations

    ebn0s, K, n_frames = [0.0, 6.0], 1200, 300
    n_bits = K * n_frames
    res = modulations.run(ebn0s, K=K, n_frames=n_frames)
    bpsk = modulations.theory("BPSK", ebn0s)
    for name, model in (("BPSK", 0.0), ("QPSK", 0.0), ("16-QAM", 0.1)):  # 16-QAM: nearest-neighbour approximation
        for got, th in zip(res[f"{name}, AWGN"], modulations.theory(name, ebn0s)):
            assert near_theory(got, th, n_bits, model), (name, got, th)
    assert modulations.theory("QPSK", ebn0s) == pytest.approx(bpsk)  # same BER per Eb/N0
    rayleigh = 0.5 * (1 - math.sqrt(10**0.6 / (1 + 10**0.6)))  # BPSK over Rayleigh at 6 dB
    for name in ("BPSK", "QPSK"):
        assert near_theory(res[f"{name}, Rayleigh"][1], rayleigh, n_bits), name


def test_constellation_figure(tmp_path):
    pytest.importorskip("matplotlib")
    import modulations

    modulations.plot_constellation(tmp_path / "qam.svg")
    assert (tmp_path / "qam.svg").stat().st_size > 1000


def test_fixed_point():
    import fixed_point

    res = fixed_point.run(ebn0s=[2.0], max_fe=100)
    for label, (fer,) in res.items():
        ref = f"POLAR/AWGN/BPSK/SC/Polar_N128_K96_SC_NO_SYS_{fixed_point.REFERENCES[label]}.txt"
        near_reference(ref, 2.0, fer, int(100 / max(fer, 1e-3)))


def test_polar_codes():
    import polar_codes

    res, out = quiet(polar_codes.run)
    fb = res["frozen"]["frozen_bits"]
    assert fb.dtype == np.bool_ and fb.sum() == 16 and not fb[-1]
    assert sorted(res["frozen"]["best"].tolist()) == list(range(32))
    assert res["frozen"]["fb_rm"].sum() == 16
    assert "False" in out  # a repetition decoder has no frozen bits
    f1, f3 = res["clones"]["fers"]
    assert f3 < f1


def test_command_line():
    import command_line

    res, out = quiet(command_line.run)
    assert res["parameters"]["L"] == 4 and res["headers"]["dec"]["Num. of lists (L)"] == "4"
    assert "--crc-poly" in out  # help of the CRC factory


def test_ldpc_matrices():
    import ldpc_matrices

    res, _ = quiet(ldpc_matrices.run)
    np.testing.assert_array_equal(res["v"], res["u"])
    assert res["H2"].shape == (3, 7) and len(res["info_bits_pos"]) == 4


def test_turbo_lte():
    import turbo_lte

    cdc_k, crc_k = turbo_lte.codec_from_keywords()
    cdc_c, crc_c = turbo_lte.codec_from_command_line()
    assert (cdc_k.puncturer.N, cdc_k.encoder.N, crc_k.size) == (cdc_c.puncturer.N, cdc_c.encoder.N, crc_c.size)
    (fer,) = turbo_lte.simulate(cdc_k, crc_k, [1.0], max_fe=50, n_threads=2)
    near_reference("TURBO/AWGN/BPSK/RSC_RSC/BCJR/LTE/Turbo_N4096_K2048_BCJR_i8_ref_LTE.txt", 1.0, fer, int(50 / fer))


def test_ldpc_bfer():
    import ldpc_bfer

    H = Path(__file__).resolve().parent.parent / "lib" / "aff3ct" / "conf" / "dec" / "LDPC" / "CCSDS_64_128.alist"
    if not H.exists():
        pytest.skip("lib/aff3ct/conf not checked out")
    res, _ = quiet(ldpc_bfer.simulate, str(H), [2.0], max_fe=100, n_threads=2, quiet=True)
    (_ebn0, _ber, fer, frames), = res
    near_reference("LDPC/AWGN/BPSK/BP_HORIZONTAL_LAYERED/SPA/LDPC_N128_K64_hlayered_SPA_i50_CCSDS.txt", 2.0, fer, frames)


def test_seed_sequence_gives_each_thread_its_own_values():
    import numpy as np
    import streampu as spu

    import aff3ct as af

    K = 64
    src, chn = af.src.source(K, type="RAND", seed=3), af.chn.channel(K, type="AWGN", seed=3)
    mdm = af.mdm.modem(K, type="BPSK")
    s = spu.array([1.0], dtype=spu.float32)
    chn.add_noise(s, mdm.modulate(src.generate()[0]))
    seq = spu.Sequence(chn["add_noise::Y_N"], n_threads=3)

    def draws():
        z = spu.array(np.zeros(K, dtype=np.float32), dtype=spu.float32)
        return ([c.generate()[0].numpy.copy() for c in seq.get_cloned_modules(src)],
                [c.add_noise(s, z).numpy.copy() for c in seq.get_cloned_modules(chn)])

    bits, noise = draws()  # clones: copies of the same generators
    assert all((b == bits[0]).all() for b in bits) and all(np.allclose(n, noise[0]) for n in noise)
    seeds = af.tools.seed_sequence(seq, seed=1)
    assert len(seeds) == 6 and len(set(seeds)) == 6 and seeds == af.tools.seed_sequence(seq, seed=1)
    bits, noise = draws()
    assert not (bits[1] == bits[0]).all() and not np.allclose(noise[1], noise[0])


def test_polar_variants():
    import polar_variants

    if not polar_variants.available():
        pytest.skip("configuration files of AFF3CT not fetched (scripts/fetch_aff3ct_data.sh)")
    res = polar_variants.run(ebn0s=[1.0, 2.0], max_fe=50)
    assert len(res) == 3
    for name, (fer_1, fer_2) in res.items():
        assert 0 < fer_2 < fer_1 < 0.5, (name, fer_1, fer_2)
