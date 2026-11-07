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


def run_codec(cdc, ebn0s, max_fe, crc=None, n_threads=1):
    """BFER chain around a codec: src -> [crc] -> enc -> pct -> BPSK -> AWGN -> depct -> dec -> [crc] -> monitor."""
    enc, pct, dec = cdc.encoder, cdc.puncturer, cdc.decoder_siho
    K_info = enc.K - (crc.size if crc is not None else 0)
    N = pct.N if pct is not None else enc.N
    src = af.src.source(K_info, type="RAND", seed=0)
    mdm, chn = af.mdm.modem(N, type="BPSK"), af.chn.channel(N, type="AWGN", seed=1)
    mnt = af.mnt.Monitor_BFER_AR(K_info, max_fe)
    sigma = spu.array([1.0], dtype=spu.float32)
    u = src.generate()[0]
    x = enc.encode(crc.build(u) if crc is not None else u)
    if pct is not None:
        x = pct.puncture(x)
    y = mdm.demodulate(sigma, chn.add_noise(sigma, mdm.modulate(x)))
    if pct is not None:
        y = pct.depuncture(y)
    dec.decode_siho(y)
    v = dec["decode_siho::V_K"]
    mnt.check_errors(u, crc.extract(v) if crc is not None else v)
    seq = spu.Sequence(mnt["check_errors::status"], n_threads=n_threads)
    out = []
    for ebn0 in ebn0s:
        s = af.tools.sigma_from_ebn0(ebn0, K_info / N)
        sigma.numpy[...] = s.sigma
        cdc.set_noise(s)  # modules of the codec only (not their clones): enough for these codes
        mnt.reset()
        seq.exec()
        out.append((ebn0, mnt.ber, mnt.fer, mnt.n_analyzed_frames))
    return out


def test_ra_codec_matches_the_reference():
    ref = read_ref(REFS / "RA/AWGN/BPSK/RA_N4096_K1024_MS_i10.txt")
    cdc = af.codec.ra(1024, 4096, itl_core_type="RANDOM", itl_core_seed=0, dec_n_ite=10)
    assert isinstance(cdc, af.codec.Codec_RA) and cdc.interleaver is not None
    ebn0s = [1.3, 1.5]
    check(run_codec(cdc, ebn0s, max_fe=150, n_threads=4), ref, ebn0s)


def test_turbo_lte_codec_with_crc_and_puncturer_matches_the_reference():
    # aff3ct -C TURBO -K 2048 --enc-sub-std LTE -i 8 --dec-sf-type LTE_VEC --dec-sub-implem FAST --dec-sub-max MAX
    #        --pct-pattern "11,10,01" --crc-implem FAST --crc-poly 24-LTEA
    ref = read_ref(REFS / "TURBO/AWGN/BPSK/RSC_RSC/BCJR/LTE/Turbo_N4096_K2048_BCJR_i8_ref_LTE.txt")
    K = 2048
    crc = af.crc.crc(K - 24, type="24-LTEA", implem="FAST")
    cdc = af.codec.turbo(K, 3 * K + 12, crc, N=4108, enc_sub_standard="LTE", dec_n_ite=8,
                         dec_sf_enable=True, dec_sf_type="LTE_VEC",  # --dec-sf-type also enables it on the command line
                         dec_sub_implem="FAST", dec_sub_max="MAX",
                         pct_pattern=[[True, True], [True, False], [False, True]])  # "11,10,01"
    assert af.codec.turbo.factory(K, 3 * K + 12, N=4108, pct_pattern=[[1, 1], [1, 0], [0, 1]]).headers()["pct"][
        "Pattern"] == "{11,10,01}"
    assert isinstance(cdc, af.codec.Codec_turbo) and (cdc.puncturer.N, cdc.encoder.N) == (4108, 3 * K + 12)
    ebn0s = [0.9, 1.0]
    check(run_codec(cdc, ebn0s, max_fe=100, crc=crc, n_threads=4), ref, ebn0s)


# ----------------------------------------------------------------------------------------------- modems and channels
def read_ref_cols(path: Path, noise_col: int, fra_col: int, ber_col: int) -> dict[float, tuple[int, float]]:
    """{noise: (FRA, BER)} of a reference file (columns of the noise, of FRA and of BER)."""
    pts = {}
    for line in path.read_text().splitlines():
        if line.startswith("#"):
            continue
        cols = [c.strip() for c in re.split(r"\|\|?", line)]
        try:
            pts[round(float(cols[noise_col]), 4)] = (int(cols[fra_col]), float(cols[ber_col]))
        except (ValueError, IndexError):
            continue
    return pts


def check_ber(measured, ref, K):
    for noise, ber, fra in measured:
        r_fra, r_ber = ref[round(noise, 4)]
        sd = math.sqrt(r_ber * (1 - r_ber) / (r_fra * K) + ber * (1 - ber) / (fra * K))
        assert abs(ber - r_ber) <= 5 * sd + 1e-4, (noise, ber, r_ber, sd)


def run_uncoded(K, mdm, chn, noises, to_cp, n_frames, with_gains=False, event_probability=False):
    """Uncoded chain src -> modulate -> channel -> demodulate -> hard decision -> monitor; [(noise, BER, FRA)]."""
    src = af.src.source(K, type="RAND", seed=0)
    # as the simulator: with an event probability noise (BEC, BSC), the erased bits count as errors
    mnt = af.mnt.Monitor_BFER_AR(K, max_fe=10**9, max_n_frames=n_frames, count_unknown_values=event_probability)
    cp = spu.array([1.0], dtype=spu.float32)
    u = src.generate()[0]
    if with_gains:
        chn.add_noise_wg(cp, mdm.modulate(u))
        llr = mdm.demodulate_wg(cp, chn["add_noise_wg::H_N"], chn["add_noise_wg::Y_N"])
    else:
        llr = mdm.demodulate(cp, chn.add_noise(cp, mdm.modulate(u)))
    cdc = af.codec.uncoded(K, K)  # as the simulator for UNCODED: hard decision
    dec = cdc.decoder_siho
    dec.decode_siho(llr)
    mnt.check_errors(u, dec["decode_siho::V_K"])
    seq = spu.Sequence(mnt["check_errors::status"], n_threads=4)
    out = []
    for n in noises:
        cp.numpy[...] = to_cp(n)
        mnt.reset()
        seq.exec()
        out.append((n, mnt.ber, mnt.n_analyzed_frames))
    return out


def test_qam16_awgn_matches_the_reference():
    ref = read_ref_cols(REFS / "UNCODED/AWGN/QAM/Uncoded_K4003_QAM_max_bps4.txt", 1, 2, 5)
    K = 4003
    mdm = af.mdm.modem(K, type="QAM", bps=4, max="MAX")
    assert isinstance(mdm.N_mod, int) and mdm.N_mod == 2 * math.ceil(K / 4)  # complex symbols: 2 reals
    chn = af.chn.channel(mdm.N_mod, type="AWGN", implem="FAST", seed=1)
    run = run_uncoded(K, mdm, chn, [0.0, 4.0, 8.0], lambda e: af.tools.sigma_from_ebn0(e, 1.0, bps=4).sigma, 200)
    check_ber(run, ref, K)


def test_psk4_rayleigh_matches_the_reference():
    ref = read_ref_cols(REFS / "UNCODED/RAYLEIGH/PSK/Uncoded_K4003_PSK_max_bps2.txt", 1, 2, 5)
    K = 4003
    mdm = af.mdm.modem(K, type="PSK", bps=2)
    chn = af.chn.channel(mdm.N_mod, type="RAYLEIGH", implem="FAST", complex=True, seed=1)
    run = run_uncoded(K, mdm, chn, [0.0, 6.0, 12.0], lambda e: af.tools.sigma_from_ebn0(e, 1.0, bps=2).sigma, 200,
                      with_gains=True)
    check_ber(run, ref, K)


@pytest.mark.parametrize("channel", ["BEC", "BSC"])
def test_ook_erasure_and_symmetric_channels_match_the_reference(channel):
    ref = read_ref_cols(REFS / f"UNCODED/{channel}/OOK/Uncoded_K128_OOK.txt", 0, 1, 4)
    K = 128
    mdm = af.mdm.modem(K, type="OOK", channel_type=channel)
    chn = af.chn.channel(K, type=channel, seed=1)
    run = run_uncoded(K, mdm, chn, [0.1, 0.3], lambda p: p, 2000, event_probability=True)
    check_ber(run, ref, K)
