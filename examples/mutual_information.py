#!/usr/bin/env python3
"""Mutual information and EXIT measures (docs/guides/monitors.md).

The mutual information between the bits and the LLRs of a BPSK demodulator over AWGN is the capacity of the binary
input AWGN channel: measured with af.mnt.mi on 4 threads (the measures of the threads summed by af.mnt.reduce) and
compared with the theory.

    python examples/mutual_information.py [--plot capacity.svg]
"""

from __future__ import annotations

import argparse

import numpy as np
import streampu as spu

import aff3ct as af


def theory(esn0s) -> list[float]:
    """Capacity of the binary input AWGN channel (bits per channel use), numerical integration."""
    out = []
    for e in esn0s:
        s2 = 1 / (2 * 10 ** (e / 10))  # noise variance, unit energy symbols
        mu = 2 / s2  # the LLRs are Gaussian, mean 2 / s2 and variance 4 / s2 (bit 0)
        x = np.linspace(mu - 12 * np.sqrt(2 * mu), mu + 12 * np.sqrt(2 * mu), 20001)
        pdf = np.exp(-((x - mu) ** 2) / (4 * mu)) / np.sqrt(4 * np.pi * mu)
        out.append(float(1 - np.trapezoid(pdf * np.logaddexp(0, -x) / np.log(2), x)))
    return out


def measure(esn0s, N: int = 16384, n_frames: int = 100, n_threads: int = 4) -> list[float]:
    # --8<-- [start:mi]
    src = af.src.source(N, type="RAND")
    mdm, chn = af.mdm.modem(N, type="BPSK"), af.chn.channel(N, type="AWGN")
    mnt = af.mnt.mi(N, n_trials=n_frames)  # estimated frame by frame (long frames: small bias); n_frames per thread
    sigma = spu.array([1.0], dtype=spu.float32)
    u = src.generate()[0]
    llr = mdm.demodulate(sigma, chn.add_noise(sigma, mdm.modulate(u)))
    mnt.get_mutual_info(u, llr)  # mutual information between the bits and their LLRs
    seq = spu.Sequence(mnt["get_mutual_info::status"], n_threads=n_threads)
    af.tools.seed_sequence(seq)
    mi = []
    for e in esn0s:
        sigma.numpy[...] = af.tools.sigma_from_ebn0(e).sigma  # rate 1, 1 bit per symbol: Es/N0 = Eb/N0
        for clone in seq.get_cloned_modules(mnt):
            clone.reset()
        seq.exec()
        mi.append(af.mnt.reduce(seq, mnt).mi)  # mean over the frames of all the threads
    # --8<-- [end:mi]
    return mi


def plot(esn0s, measured, path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    th = np.linspace(min(esn0s), max(esn0s), 200)
    ax.plot(th, theory(th), color="0.4", lw=1.5, label="BI-AWGN capacity (theory)")
    ax.plot(esn0s, measured, "o", color="C0", label="af.mnt.mi, BPSK demodulator")
    ax.set_xlabel("Es/N0 (dB)")
    ax.set_ylabel("Mutual information (bit)")
    ax.set_ylim(0, 1.02)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--plot", help="output figure (svg, png...)")
    a = p.parse_args()
    esn0s = [-10.0, -7.5, -5.0, -2.5, 0.0, 2.5, 5.0]
    mi = measure(esn0s)
    for e, m, t in zip(esn0s, mi, theory(esn0s)):
        print(f"Es/N0 = {e:5.1f} dB   MI = {m:.4f}   capacity = {t:.4f}")
    if a.plot:
        plot(esn0s, mi, a.plot)
