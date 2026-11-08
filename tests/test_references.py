"""BER/FER of complete chains compared to the AFF3CT references (lib/aff3ct/refs, Plan.md phase 2).

Each point is simulated with fewer frame errors than the reference: the measured FER must be within 4 standard
deviations (binomial, measure and reference combined) of the reference one. Skipped when the ``refs`` submodule of
AFF3CT is not checked out (``git -C lib/aff3ct submodule update --init refs``).
"""

from __future__ import annotations

import math
import re
import shlex
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
    out = []
    for ebn0 in ebn0s:
        s = af.tools.sigma_from_ebn0(ebn0, K_info / N)
        sigma.numpy[...] = s.sigma
        cdc.set_noise(s)  # modules of the codec only (frozen bits of the polar codes...):
        seq = spu.Sequence(mnt["check_errors::status"], n_threads=n_threads)  # cloned after
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


# ----------------------------------------------------------------------------------------------- from the command line
CODECS_OF_CLI = {"POLAR": "Codec_polar", "CONV": "Codec_conv", "RSC": "Codec_RSC", "REP": "Codec_repetition",
                 "LDPC": "Codec_LDPC", "BCH": "Codec_BCH", "RS": "Codec_RS", "TURBO": "Codec_turbo", "RA": "Codec_RA",
                 "RSC_DB": "Codec_RSC_DB", "TURBO_DB": "Codec_turbo_DB", "TPC": "Codec_turbo_product"}
CONF_FILES = ("CCSDS_64_128.alist", "WIMAX_288_576.alist", "MACKAY_504_1008.alist", "PEG_Reg_1008x504.alist")


def reference_args(path: Path) -> list[str]:
    """AFF3CT command line of a reference, the paths of the configuration files made absolute."""
    cmd = next(line for line in path.read_text().splitlines() if line.startswith("command="))[len("command="):]
    args = shlex.split(cmd)[1:]
    conf = REFS.parent / "conf"
    return [str(conf / a[len("conf/"):]) if a.startswith("conf/") else a for a in args]


def option(args, *names, default=None):
    for n in names:
        if n in args:
            return args[args.index(n) + 1]
    return default


# precision (-p) -> (B, R, Q) dtypes of the simulator
PRECISIONS = {"8": (spu.int8, spu.float32, spu.int8), "08": (spu.int8, spu.float32, spu.int8),
              "16": (spu.int16, spu.float32, spu.int16), "32": (spu.int32, spu.float32, spu.float32),
              "64": (spu.int64, spu.float64, spu.float64)}
# fixed-point quantizer defaults of the AFF3CT launchers (src/Launcher/Code/*/*.cpp): {code: {Q: (bits, decimals)}}
QNT_DEFAULTS = {"POLAR": {spu.int8: (6, 1), spu.int16: (6, 1)}, "RSC": {spu.int8: (6, 1), spu.int16: (6, 3)},
                "RSC_DB": {spu.int8: (6, 1), spu.int16: (6, 3)}, "LDPC": {spu.int8: (6, 2), spu.int16: (6, 2)},
                "REP": {spu.int8: (6, 2), spu.int16: (6, 2)}}


def run_reference(path: Path, points, max_fe, n_threads=4):
    """The BFER chain of a reference built from its command line: each factory (source, CRC, codec, modem, channel)
    takes its own arguments (from_cli(..., strict=False)), the sizes are propagated as by the AFF3CT simulator.
    Returns [(noise, BER, FER, frames)]."""
    args = reference_args(path)
    for a in args:
        if a.endswith((".alist", ".qc")) and not Path(a).exists():
            pytest.skip(f"{a} not checked out (lib/aff3ct/conf)")
    code = option(args, "-C", "--sim-cde-type")
    B, R, Q = PRECISIONS[option(args, "-p", "--sim-prec", default="32")]
    fac = getattr(af.factory, CODECS_OF_CLI[code])()
    if code in ("POLAR", "TURBO", "TURBO_DB", "LDPC"):
        fac.enable_puncturer()  # as the BFER launchers of AFF3CT for these codes (-N is then the frame size)
    fac.from_cli(args, strict=False)
    if option(args, "--src-type") == "AZCW":  # as BFER_std.cpp: all-zero source <=> all-zero encoder
        fac.enc.type = "AZCW"
    probe = fac.clone()
    probe._complete()
    crc = None
    if any(a.startswith("--crc-") for a in args):
        crc_fac = af.factory.CRC.from_cli(args, strict=False)
        crc_fac._complete()
        crc_fac.K = probe.K - crc_fac.size
        crc = crc_fac.build(B=B)
    cdc = fac.build(crc, B=B, Q=Q) if crc is not None else fac.build(B=B, Q=Q)
    enc, pct, dec = cdc.encoder, cdc.puncturer, cdc.decoder_siho
    K_info = enc.K - (crc.size if crc is not None else 0)
    N = pct.N if pct is not None else enc.N

    ep = option(args, "-E", "--sim-noise-type") == "EP"
    # sizes set after the command line (-K, -N are also arguments of these factories); all-zero codewords: source too
    src_fac = af.factory.Source.from_cli(args, strict=False)
    src_fac.K = K_info
    if probe.enc.type == "AZCW":
        src_fac.type = "AZCW"
    src = src_fac.build(B=B)
    mdm_fac = af.factory.Modem.from_cli(args, strict=False)
    mdm_fac.N = N
    chn_type = option(args, "--chn-type", default="AWGN")
    mdm_fac.channel_type = chn_type
    mdm_probe = mdm_fac.clone()
    mdm_probe._complete()
    if mdm_probe.type in ("PSK", "PAM", "QAM", "USER"):  # generic modem: its constellation (kept alive by the modem)
        mdm = mdm_fac.build(mdm_fac.build_constellation(R=R), B=B, R=R, Q=R)
    else:
        mdm = mdm_fac.build(B=B, R=R, Q=R)
    chn_fac = af.factory.Channel.from_cli(args, strict=False)
    chn_fac.N, chn_fac.seed, chn_fac.complex = mdm.N_mod, 1, mdm_probe.complex  # as the simulator
    chn = chn_fac.build(R=R)
    qnt = None
    if Q in (spu.int8, spu.int16):  # fixed point: LLRs quantized after the demodulator, as BFER_std.cpp
        qnt_fac = af.factory.Quantizer()
        qnt_fac.n_bits, qnt_fac.n_decimals = QNT_DEFAULTS.get(code, {}).get(Q, (qnt_fac.n_bits, qnt_fac.n_decimals))
        qnt_fac.from_cli(args, strict=False)
        qnt_fac.size = N
        qnt = qnt_fac.build(R=R, Q=Q)
    mnt = af.mnt.Monitor_BFER_AR[B](K_info, max_fe, count_unknown_values=ep)

    cp = spu.array([1.0], dtype=R)
    u = src.generate()[0]
    x = enc.encode(crc.build(u) if crc is not None else u)
    if pct is not None:
        x = pct.puncture(x)
    y = mdm.demodulate(cp, chn.add_noise(cp, mdm.modulate(x)))
    if qnt is not None:
        y = qnt.process(y)
    if pct is not None:
        y = pct.depuncture(y)
    dec.decode_siho(y)
    v = dec["decode_siho::V_K"]
    mnt.check_errors(u, crc.extract(v) if crc is not None else v)
    out = []
    for p in points:
        if ep:
            noise = af.tools.Event_probability[R](p)
            cp.numpy[...] = p
        else:
            # bits per symbol and samples per symbol of the modem, as Noise.cpp of the simulator
            upf = mdm_probe.cpm_upf if mdm_probe.type == "CPM" else 1
            noise = af.tools.sigma_from_ebn0(p, K_info / N, bps=mdm_probe.bps, upsample_factor=upf, R=R)
            cp.numpy[...] = noise.sigma
        cdc.set_noise(noise)  # modules of the codec (frozen bits of the polar codes...), cloned below
        seq = spu.Sequence(mnt["check_errors::status"], n_threads=n_threads)
        af.tools.seed_sequence(seq)  # as the simulator: each thread its own frames and noise
        mnt.reset()
        seq.exec()
        out.append((p, mnt.ber, mnt.fer, mnt.n_analyzed_frames))
    return out


def read_ref_ep(path: Path) -> dict[float, tuple[int, int, float]]:
    """{event probability: (FRA, FE, FER)} of a reference with an EP noise (no Es/N0, Eb/N0 columns)."""
    pts = {}
    for line in path.read_text().splitlines():
        cols = [c.strip() for c in re.split(r"\|\|?", line)]
        if len(cols) >= 6 and re.fullmatch(r"[0-9.]+", cols[0] or "x") and re.fullmatch(r"[0-9]+", cols[1] or "x"):
            pts[float(cols[0])] = (int(cols[1]), int(cols[3]), float(cols[5]))
    return pts


@pytest.mark.parametrize(
    "ref, points, max_fe",
    [
        # polar: CA-SCL (adaptive SCL, 24-LTEA CRC, SPC nodes), shortening of the last bits
        ("POLAR/AWGN/BPSK/ASCL/Polar_N160_K40_ASCL_FA_L32_CRC24_SPC4_p32.txt", [2.0, 3.0], 150),
        ("CONV/AWGN/BPSK/Viterbi/CONV_N140_K64_Viterbi_p32.txt", [1.0, 2.0], 150),
        ("RSC/AWGN/BPSK/BCJR/RSC_N2056_K1024_BCJR_p32.txt", [0.5, 1.0], 150),
        ("REP/AWGN/BPSK/Repetition_N4096_K128_STD_p32.txt", [2.0, 4.0], 150),
        # LDPC decoders (all-zero codewords as the references)
        ("LDPC/AWGN/BPSK/BP_FLOODING/SPA/LDPC_N576_K288_flooding_SPA_i100_WiMAX.txt", [1.0, 1.5], 150),
        ("LDPC/AWGN/BPSK/BP_FLOODING/AMS/LDPC_N576_K288_flooding_AMS_minstar_i100_WiMAX.txt", [1.0, 1.5], 150),
        ("LDPC/AWGN/BPSK/BP_FLOODING/AMS/LDPC_N576_K288_flooding_AMS_min_i100_WiMAX.txt", [1.25, 1.75], 150),
        ("LDPC/AWGN/BPSK/BP_HORIZONTAL_LAYERED/NMS/LDPC_N576_K288_hlayered_NMS_i100_WiMAX.txt", [1.0, 1.5], 150),
        # Gallager decoders: steep curves, references with few frames: more frame errors
        ("LDPC/AWGN/BPSK/BP_FLOODING/GALA/LDPC_N1008_K504_flooding_GALA_i200_MacKay.txt", [4.75, 5.25], 300),
        ("LDPC/AWGN/BPSK/BP_FLOODING/GALB/LDPC_N1008_K504_flooding_GALB_i200_MacKay.txt", [4.75, 5.25], 300),
        ("LDPC/AWGN/BPSK/BP_FLOODING/GALE/LDPC_N1008_K504_flooding_GALE_i200_MacKay.txt", [2.0, 3.0], 300),
        ("LDPC/AWGN/BPSK/BIT_FLIPPING/WBF/LDPC_N1008_K504_WBF_i100.txt", [2.0, 3.0], 150),
        ("LDPC/AWGN/BPSK/BIT_FLIPPING/MWBF/LDPC_N1008_K504_MWBF02_i100.txt", [2.0, 3.0], 150),
        # fixed point (8 and 16 bits): quantizer after the demodulator
        ("POLAR/AWGN/BPSK/SC/Polar_N128_K96_SC_NO_SYS_p08.txt", [1.0, 2.0], 150),
        ("POLAR/AWGN/BPSK/SC/Polar_N128_K96_SC_NO_SYS_p16.txt", [1.0, 2.0], 150),
        ("RSC/AWGN/BPSK/BCJR/RSC_N2056_K1024_BCJR_p08.txt", [0.5, 1.0], 150),
        ("RSC/AWGN/BPSK/BCJR/RSC_N2056_K1024_BCJR_p16.txt", [0.5, 1.0], 150),
        ("REP/AWGN/BPSK/Repetition_N4096_K128_FAST_p16.txt", [2.0, 4.0], 150),
        ("REP/AWGN/BPSK/Repetition_N4096_K128_FAST_p08.txt", [2.0, 4.0], 150),
        ("POLAR/AWGN/BPSK/SCAN/Polar_N2048_K1723_SCAN_GA_naive_i4_p16.txt", [3.0, 3.5], 100),
        # double-binary RSC (DVB-RCS2)
        ("RSC_DB/AWGN/BPSK/RSC_DB_N2048_K1024_BCJR_p08.txt", [3.0, 4.0], 150),
        ("RSC_DB/AWGN/BPSK/RSC_DB_N2048_K1024_BCJR_p16.txt", [3.0, 4.0], 150),
        # double-binary turbo codes (DVB-RCS1 / RCS2, QPSK, CRC, adaptive scaling factor, flip and check)
        ("TURBO_DB/AWGN/BPSK/RSC_DB_RSC_DB/BCJR/Turbo_DB_N2256_K1504_BCJR_i8_ref_DVB-RCS2.txt", [2.0, 2.4], 100),
        ("TURBO_DB/AWGN/BPSK/RSC_DB_RSC_DB/BCJR/Turbo_DB_N3008_K1504_BCJR_i8_fnc_DVB-RCS1.txt", [1.2, 1.4], 100),
        # turbo product codes (extended BCH, Chase-Pyndiah)
        ("TURBO_PROD/AWGN/BPSK/BCH1/Turbo_prod_BCH_16_11_p5_i8.txt", [1.0, 1.5], 150),
        ("TURBO_PROD/AWGN/BPSK/BCH2/Turbo_prod_BCH_32_21_p5_i8.txt", [1.0, 1.25], 150),
        # algebraic BCH and RS
        ("BCH/AWGN/BPSK/ALGEBRAIC/BCH_N127_K120_algebraic_T1.txt", [5.0, 6.0], 150),
    ],
)
def test_chains_from_the_reference_command_lines(ref, points, max_fe):
    check(run_reference(REFS / ref, points, max_fe), read_ref(REFS / ref), points)


@pytest.mark.parametrize(
    "ref, points",
    [
        ("LDPC/BEC/OOK/BP_HORIZONTAL_LAYERED/NMS/LDPC_N576_K288_hlayered_NMS_i100_WiMAX.txt", [0.44, 0.42]),
        ("LDPC/BSC/OOK/BP_HORIZONTAL_LAYERED/NMS/LDPC_N576_K288_hlayered_NMS_i100_WiMAX.txt", [0.07, 0.06]),
        ("RS/BSC/OOK/ALGEBRAIC/RS_N63_K59_algebraic_T2.txt", [0.01, 0.05]),
        ("RS/BEC/OOK/ALGEBRAIC/RS_N63_K59_algebraic_T2.txt", [0.01, 0.05]),
        ("BCH/BSC/OOK/ALGEBRAIC/BCH_N255_K131_algebraic_T18.txt.txt", [0.06, 0.08]),
        ("TURBO_DB/BEC/OOK/RSC_DB_RSC_DB/BCJR/Turbo_DB_N3008_K1504_BCJR_i8_DVB-RCS1.txt", [0.47, 0.46]),
    ],
)
def test_erasure_and_symmetric_channels_from_the_reference_command_lines(ref, points):
    ref_pts = read_ref_ep(REFS / ref)
    measured = run_reference(REFS / ref, points, max_fe=150)
    check(measured, {round(p, 4): v for p, v in ref_pts.items()}, points)
