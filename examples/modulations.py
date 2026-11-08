#!/usr/bin/env python3
"""Generic modems and channels: constellations, uncoded BER over AWGN and Rayleigh (docs/guides/modems.md).

    python examples/modulations.py --plot ber.svg --plot-constellation qam16.svg
"""

from __future__ import annotations

import argparse
import math

import numpy as np
import streampu as spu

import aff3ct as af


def uncoded_ber(mdm, bps, chn, ebn0s, K, n_frames=200, rayleigh=False) -> list[float]:
    """BER of an uncoded chain: source, modulation, channel, demodulation, hard decision."""
    # --8<-- [start:uncoded]
    src = af.src.source(K, type="RAND", seed=0)
    dec = af.codec.uncoded(K, K).decoder_siho  # hard decision on the LLRs
    mnt = af.mnt.Monitor_BFER_AR(K, max_fe=10**9, max_n_frames=n_frames)
    sigma = spu.array([1.0], dtype=spu.float32)

    u = src.generate()[0]
    if rayleigh:  # the channel also outputs its gains H, given to the demodulator
        chn.add_noise_wg(sigma, mdm.modulate(u))
        llr = mdm.demodulate_wg(sigma, chn["add_noise_wg::H_N"], chn["add_noise_wg::Y_N"])
    else:
        llr = mdm.demodulate(sigma, chn.add_noise(sigma, mdm.modulate(u)))
    _, v = dec.decode_siho(llr)
    mnt.check_errors(u, v)
    seq = spu.Sequence(mnt["check_errors::status"], n_threads=2)
    af.tools.seed_sequence(seq)  # each thread its own frames and noise

    ber = []
    for ebn0 in ebn0s:
        sigma.numpy[...] = af.tools.sigma_from_ebn0(ebn0, code_rate=1.0, bps=bps).sigma
        mnt.reset()
        seq.exec()
        ber.append(mnt.ber)
    # --8<-- [end:uncoded]
    return ber


def theory(name: str, ebn0s) -> list[float]:
    """Theoretical BER over AWGN (Gray mapping, high SNR approximation for 16-QAM)."""
    q = lambda x: 0.5 * math.erfc(x / math.sqrt(2))  # noqa: E731
    g = [10 ** (e / 10) for e in ebn0s]
    if name in ("BPSK", "QPSK"):
        return [q(math.sqrt(2 * x)) for x in g]
    if name == "16-QAM":
        return [0.75 * q(math.sqrt(0.8 * x)) for x in g]
    raise ValueError(name)


def run(ebn0s=(0.0, 2.0, 4.0, 6.0, 8.0), K=1200, n_frames=200) -> dict[str, list[float]]:
    # --8<-- [start:modems]
    modems = {  # name: (modem, bits per symbol, complex symbols)
        "BPSK": (af.mdm.modem(K, type="BPSK"), 1, False),
        "QPSK": (af.mdm.modem(K, type="PSK", bps=2), 2, True),  # the constellation is built by the modem
        "16-QAM": (af.mdm.modem(K, type="QAM", bps=4), 4, True),
        "8-PSK (symbols)": (af.mdm.modem(K, symbols=np.exp(2j * np.pi * np.arange(8) / 8)), 3, True),  # any symbols
    }
    # --8<-- [end:modems]
    out = {}
    for name, (mdm, bps, complex_) in modems.items():
        # N_mod: size of the modulated frame (complex symbols: real and imaginary parts interleaved)
        # --8<-- [start:channels]
        awgn = af.chn.channel(mdm.N_mod, type="AWGN", complex=complex_, seed=1)
        rayleigh = af.chn.channel(mdm.N_mod, type="RAYLEIGH", complex=complex_, seed=1)
        # --8<-- [end:channels]
        out[f"{name}, AWGN"] = uncoded_ber(mdm, bps, awgn, ebn0s, K, n_frames)
        out[f"{name}, Rayleigh"] = uncoded_ber(mdm, bps, rayleigh, ebn0s, K, n_frames, rayleigh=True)
    return out


def plot_constellation(path, bps=4):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # --8<-- [start:constellation]
    cstl = af.tools.Constellation_QAM(bps)
    symbols = cstl.symbols  # numpy.ndarray[complex64], unit mean energy
    # the symbol i is the image of the bits of i, the first bit being the least significant one
    labels = ["".join(str((i >> j) & 1) for j in range(bps)) for i in range(cstl.n_symbols)]
    # --8<-- [end:constellation]
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    ax.scatter(symbols.real, symbols.imag)
    for s, lab in zip(symbols, labels):
        ax.annotate(lab, (s.real, s.imag), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8)
    ax.set_aspect("equal")
    ax.axhline(0, color="gray", lw=0.5)
    ax.axvline(0, color="gray", lw=0.5)
    ax.set_title("16-QAM (bits in transmission order)")
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.3, 1.3)
    fig.tight_layout()
    fig.savefig(path)


def plot(results, ebn0s, path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4.5))
    colors = {}
    for label, ber in results.items():
        name, chn = label.split(", ")
        line = ax.semilogy(ebn0s, ber, "o-" if chn == "AWGN" else "s--", label=label, color=colors.get(name))
        colors[name] = line[0].get_color()
    for name in ("BPSK", "16-QAM"):
        ax.semilogy(ebn0s, theory(name, ebn0s), ":", color=colors[name], label=f"{name}, AWGN (theory)")
    ax.set_xlabel("Eb/N0 (dB)")
    ax.set_ylabel("Bit error rate")
    ax.set_title("Uncoded transmission")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(path)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--plot", help="save the BER curves in this file")
    p.add_argument("--plot-constellation", help="save the 16-QAM constellation in this file")
    a = p.parse_args()
    ebn0s = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0]
    res = run(ebn0s)
    for label, ber in res.items():
        print(f"{label:28s}", " ".join(f"{b:.2e}" for b in ber))
    if a.plot:
        plot(res, ebn0s, a.plot)
    if a.plot_constellation:
        plot_constellation(a.plot_constellation)
