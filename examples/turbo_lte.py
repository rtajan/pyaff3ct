#!/usr/bin/env python3
"""LTE turbo code with a CRC and puncturing, built from keywords or from an AFF3CT command line (docs/guides/turbo.md).

Same chain as the AFF3CT reference TURBO/AWGN/BPSK/RSC_RSC/BCJR/LTE/Turbo_N4096_K2048_BCJR_i8_ref_LTE.txt.

    python examples/turbo_lte.py --threads 4 --plot turbo.svg
"""

from __future__ import annotations

import argparse

import streampu as spu

import aff3ct as af

# --8<-- [start:command]
COMMAND = ('-C TURBO -K 2048 -N 4108 --enc-sub-std LTE -i 8 --dec-sf-type LTE_VEC --dec-sub-implem FAST '
           '--dec-sub-max MAX --pct-pattern "11,10,01" --crc-implem FAST --crc-poly 24-LTEA')
# --8<-- [end:command]


def codec_from_keywords(K=2048):
    # --8<-- [start:keywords]
    crc = af.crc.crc(K - 24, type="24-LTEA", implem="FAST")  # the 24 CRC bits are part of the K bits of the code
    cdc = af.codec.turbo(
        K, 3 * K + 12, crc,  # N_cw: 3 K + 12 tail bits
        N=4108,  # frame size after puncturing: adds the puncturer
        enc_sub_standard="LTE",  # both sub-encoders (--enc-sub-std)
        dec_n_ite=8,
        dec_sf_enable=True, dec_sf_type="LTE_VEC",  # scaling factor of the extrinsic information
        dec_sub_implem="FAST", dec_sub_max="MAX",  # max-log-MAP BCJR
        pct_pattern=[[1, 1], [1, 0], [0, 1]],  # "11,10,01": systematic bits kept, parities alternated
    )
    # --8<-- [end:keywords]
    return cdc, crc


def codec_from_command_line():
    # --8<-- [start:command_line]
    fac = af.factory.Codec_turbo()
    fac.enable_puncturer()  # as the AFF3CT launcher of the turbo codes: -N is then the frame size
    fac.from_cli(COMMAND, strict=False)
    crc_fac = af.factory.CRC.from_cli(COMMAND, strict=False)
    crc_fac.K = 2048 - 24
    crc = crc_fac.build()
    cdc = fac.build(crc)
    # --8<-- [end:command_line]
    return cdc, crc


# --8<-- [start:chain]
def simulate(cdc, crc, ebn0s, max_fe=100, n_threads=4) -> list[float]:
    enc, pct, dec = cdc.encoder, cdc.puncturer, cdc.decoder_siho
    K_info, N = enc.K - crc.size, pct.N
    src = af.src.source(K_info, seed=0)
    mdm, chn = af.mdm.modem(N), af.chn.channel(N, seed=1)
    mnt = af.mnt.Monitor_BFER_AR(K_info, max_fe)
    sigma = spu.array([1.0], dtype=spu.float32)

    u = src.generate()[0]
    x = pct.puncture(enc.encode(crc.build(u)))  # K_info -> K -> N_cw -> N bits
    y = pct.depuncture(mdm.demodulate(sigma, chn.add_noise(sigma, mdm.modulate(x))))  # N -> N_cw LLRs
    _, v = dec.decode_siho(y)  # the decoder stops early when the CRC is verified
    mnt.check_errors(u, crc.extract(v))
    seq = spu.Sequence(mnt["check_errors::status"], n_threads=n_threads)

    fer = []
    for ebn0 in ebn0s:
        sigma.numpy[...] = af.tools.sigma_from_ebn0(ebn0, K_info / N).sigma
        mnt.reset()
        seq.exec()
        fer.append(mnt.fer)
    return fer
# --8<-- [end:chain]


def plot(fer, ebn0s, path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    import _references as refs

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.semilogy(ebn0s, fer, "o", label="pyAFF3CT")
    if refs.available():
        ref = refs.read("TURBO/AWGN/BPSK/RSC_RSC/BCJR/LTE/Turbo_N4096_K2048_BCJR_i8_ref_LTE.txt")
        ax.semilogy(ref["ebn0"], ref["fer"], "-", color="C0", alpha=0.6, label="AFF3CT reference")
    ax.set_xlim(min(ebn0s) - 0.1, max(ebn0s) + 0.1)
    ax.set_xlabel("Eb/N0 (dB)")
    ax.set_ylabel("Frame error rate")
    ax.set_title("LTE turbo code, K = 2048, rate 1/2, 8 iterations")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--threads", type=int, default=4)
    p.add_argument("--max-fe", type=int, default=100)
    p.add_argument("--plot", help="save the curve in this file")
    a = p.parse_args()
    ebn0s = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1]
    cdc, crc = codec_from_keywords()
    fer = simulate(cdc, crc, ebn0s, a.max_fe, a.threads)
    print(" ".join(f"{f:.2e}" for f in fer))
    if a.plot:
        plot(fer, ebn0s, a.plot)
