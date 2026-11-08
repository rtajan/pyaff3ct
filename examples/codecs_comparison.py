#!/usr/bin/env python3
"""Comparison of codes of rate about 1/2 and K = 64 with the codecs of aff3ct.codec (docs/tutorial/codecs.md).

    python examples/codecs_comparison.py --max-fe 100 --threads 4
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import streampu as spu

import aff3ct as af

CONF = Path(__file__).resolve().parent.parent / "lib" / "aff3ct" / "conf"


def codecs(K: int = 64) -> dict[str, tuple]:
    """{label: (codec, crc)}: one codec per family, built from keyword parameters."""
    # --8<-- [start:codecs]
    out = {}
    # polar (128, 64): successive cancellation, frozen bits adapted to the noise (set_noise)
    out["Polar SC"] = (af.codec.polar(K, 2 * K, dec_type="SC", dec_implem="NAIVE"), None)
    # CRC-aided successive cancellation list (L = 8): the CRC is part of the K bits
    crc = af.crc.crc(K - 8, type="8-DVB-S2")
    out["Polar CA-SCL (L=8)"] = (af.codec.polar(K, 2 * K, crc, dec_type="SCL", dec_implem="NAIVE", dec_L=8), crc)
    # recursive systematic convolutional code, BCJR decoder (2 x 3 tail bits)
    out["RSC (BCJR)"] = (af.codec.rsc(K, 2 * K + 6), None)
    # turbo code (LTE), punctured to rate 1/2 ("11,10,01"), 6 iterations
    out["Turbo LTE (6 it.)"] = (af.codec.turbo(K, 3 * K + 12, N=2 * K + 12, enc_sub_standard="LTE", dec_n_ite=6,
                                               pct_pattern=[[1, 1], [1, 0], [0, 1]]), None)
    # repetition code
    out["Repetition"] = (af.codec.repetition(K, 2 * K), None)
    # --8<-- [end:codecs]
    H = CONF / "dec" / "LDPC" / "CCSDS_64_128.alist"
    if H.exists():  # LDPC (128, 64) of the CCSDS: belief propagation, 50 iterations
        # --8<-- [start:ldpc]
        out["LDPC CCSDS (BP)"] = (af.codec.ldpc(K, 2 * K, enc_type="LDPC_H", dec_H_path=str(H),
                                                dec_type="BP_HORIZONTAL_LAYERED", dec_implem="SPA", dec_n_ite=50), None)
        # --8<-- [end:ldpc]
    return out


# --8<-- [start:simulate]
def simulate(cdc, crc, ebn0s, max_fe=100, n_threads=1, max_frames=20_000) -> list[float]:
    """FER of a codec for each Eb/N0 (max_fe frame errors, or max_frames frames): the same chain for every codec."""
    enc, pct, dec = cdc.encoder, cdc.puncturer, cdc.decoder_siho
    K_info = enc.K - (crc.size if crc is not None else 0)  # information bits, CRC excluded
    N = pct.N if pct is not None else enc.N  # transmitted bits, after puncturing
    src = af.src.source(K_info, type="RAND", seed=0)
    mdm, chn = af.mdm.modem(N, type="BPSK"), af.chn.channel(N, type="AWGN", seed=1)
    mnt = af.mnt.Monitor_BFER_AR(K_info, max_fe, max_n_frames=max_frames)
    sigma = spu.array([1.0], dtype=spu.float32)

    u = src.generate()[0]
    x = enc.encode(crc.build(u) if crc is not None else u)
    x = pct.puncture(x) if pct is not None else x
    y = mdm.demodulate(sigma, chn.add_noise(sigma, mdm.modulate(x)))
    y = pct.depuncture(y) if pct is not None else y
    _, v = dec.decode_siho(y)
    mnt.check_errors(u, crc.extract(v) if crc is not None else v)

    fer = []
    for ebn0 in ebn0s:
        noise = af.tools.sigma_from_ebn0(ebn0, K_info / N)
        sigma.numpy[...] = noise.sigma
        cdc.set_noise(noise)  # polar codes: frozen bits for this noise
        seq = spu.Sequence(mnt["check_errors::status"], n_threads=n_threads)  # after set_noise: clones up to date
        mnt.reset()
        seq.exec()
        fer.append(mnt.fer if mnt.n_fe else float("nan"))  # no error in max_frames frames: not plotted
    return fer
# --8<-- [end:simulate]


def run(ebn0s=(1.0, 2.0, 3.0, 4.0), max_fe=100, n_threads=1, max_frames=20_000) -> dict[str, list[float]]:
    return {label: simulate(cdc, crc, ebn0s, max_fe, n_threads, max_frames) for label, (cdc, crc) in codecs().items()}


def plot(results, ebn0s, path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for label, fer in results.items():
        ax.semilogy(ebn0s, fer, "o-", label=label)
    ax.set_xlabel("Eb/N0 (dB)")
    ax.set_ylabel("Frame error rate")
    ax.set_title("K = 64, rate 1/2, BPSK over AWGN")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--max-fe", type=int, default=100)
    p.add_argument("--threads", type=int, default=1)
    p.add_argument("--plot", help="save the curves in this file")
    a = p.parse_args()
    ebn0s = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    res = run(ebn0s, a.max_fe, a.threads)
    for label, fer in res.items():
        print(f"{label:22s}", " ".join(f"{f:.2e}" for f in fer))
    if a.plot:
        plot(res, ebn0s, a.plot)
