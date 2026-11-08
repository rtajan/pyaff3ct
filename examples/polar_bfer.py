#!/usr/bin/env python3
"""BER/FER simulation of a polar code (SC decoder) over a BPSK / AWGN channel, with a streampu Sequence.

Same chain as ``aff3ct --sim-type BFER -C POLAR -K 96 -N 128 --enc-fb-gen-method GA --enc-no-sys --dec-type SC
--dec-implem NAIVE``; the reference curve is ``lib/aff3ct/refs/POLAR/AWGN/BPSK/SC/Polar_N128_K96_SC_NO_SYS_p32.txt``.

    python examples/polar_bfer.py --ebn0 1 4 0.5 --max-fe 100 --threads 4
"""

from __future__ import annotations

import argparse

import numpy as np
import streampu as spu

import aff3ct as af


# --8<-- [start:chain]
def build_chain(K: int, N: int, frozen_bits: np.ndarray, max_fe: int):
    """Modules of the chain and the sigma socket (updated in place at each SNR point)."""
    src = af.src.source(K, type="RAND", seed=0)
    enc = af.enc.polar(K, N, frozen_bits, systematic=False)
    mdm = af.mdm.modem(N, type="BPSK")
    chn = af.chn.channel(N, type="AWGN", seed=1)
    dec = af.dec.polar(K, N, frozen_bits, type="SC", implem="NAIVE", systematic=False)
    # counters shared by the clones of the threads: the sequence stops when the total reaches max_fe
    mnt = af.mnt.Monitor_BFER_AR(K, max_fe)

    sigma = spu.array([1.0], dtype=spu.float32)  # CP socket of the channel and the demodulator
    u = src.generate()[0]
    y = chn.add_noise(sigma, mdm.modulate(enc.encode(u)))
    dec.decode_siho(mdm.demodulate(sigma, y))
    mnt.check_errors(u, dec["decode_siho::V_K"])
    modules = dict(src=src, enc=enc, mdm=mdm, chn=chn, dec=dec, mnt=mnt)
    return modules, sigma
# --8<-- [end:chain]


# --8<-- [start:simulate]
def simulate(K=96, N=128, ebn0s=(1.0, 2.0, 3.0), max_fe=100, n_threads=1, quiet=False):
    """Return a list of (Eb/N0, BER, FER, number of frames)."""
    fb_gen = af.tools.Frozenbits_generator_GA_Arikan(K, N)
    modules, sigma = build_chain(K, N, fb_gen.generate(af.tools.sigma_from_ebn0(ebn0s[0], K / N)), max_fe)
    seq = spu.Sequence(modules["mnt"]["check_errors::status"], n_threads=n_threads)  # firsts found from the last socket
    af.tools.seed_sequence(seq)  # each thread its own frames and noise
    coders = seq.get_cloned_modules(modules["enc"]) + seq.get_cloned_modules(modules["dec"])
    mnt = modules["mnt"]  # shows the totals of its clones

    noise = af.tools.sigma_from_ebn0(ebn0s[0], K / N)
    reporters = [af.tools.Reporter_noise(noise), af.tools.Reporter_BFER(mnt), af.tools.Reporter_throughput(mnt)]
    ter = spu.Terminal_std(reporters)
    if not quiet:
        ter.legend()

    results = []
    for ebn0 in ebn0s:
        s = af.tools.sigma_from_ebn0(ebn0, K / N)
        noise.set_values(s.sigma, s.ebn0, s.esn0)
        sigma.numpy[...] = s.sigma
        frozen_bits = fb_gen.generate(s)  # frozen bits adapted to the noise ("--enc-fb-noise" not given)
        for c in coders:
            c.set_frozen_bits(frozen_bits)
        mnt.reset()  # resets the totals of every thread
        for r in reporters:
            r.init()
        seq.exec()  # until the total reaches max_fe
        if not quiet:
            ter.final_report()
        results.append((ebn0, mnt.ber, mnt.fer, mnt.n_analyzed_frames))
    return results
# --8<-- [end:simulate]


def plot(results, path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    import _references as refs

    ebn0s = [r[0] for r in results]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.semilogy(ebn0s, [r[2] for r in results], "o", color="C0", label="FER, pyAFF3CT")
    ax.semilogy(ebn0s, [r[1] for r in results], "s", color="C1", label="BER, pyAFF3CT")
    if refs.available():
        ref = refs.read("POLAR/AWGN/BPSK/SC/Polar_N128_K96_SC_NO_SYS_p32.txt")
        ax.semilogy(ref["ebn0"], ref["fer"], "-", color="C0", alpha=0.6, label="FER, AFF3CT reference")
        ax.semilogy(ref["ebn0"], ref["ber"], "-", color="C1", alpha=0.6, label="BER, AFF3CT reference")
    ax.set_xlim(min(ebn0s) - 0.25, max(ebn0s) + 0.25)
    ax.set_xlabel("Eb/N0 (dB)")
    ax.set_ylabel("Error rate")
    ax.set_title("Polar (128, 96), SC decoder, BPSK over AWGN")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-K", type=int, default=96)
    p.add_argument("-N", type=int, default=128)
    p.add_argument("--ebn0", type=float, nargs=3, default=(0.0, 4.0, 0.5), metavar=("MIN", "MAX", "STEP"))
    p.add_argument("--max-fe", type=int, default=100)
    p.add_argument("--threads", type=int, default=1)
    p.add_argument("--plot", help="save the curves in this file")
    a = p.parse_args()
    ebn0s = np.arange(a.ebn0[0], a.ebn0[1] + 1e-9, a.ebn0[2]).round(4).tolist()
    res = simulate(a.K, a.N, ebn0s, a.max_fe, a.threads)
    if a.plot:
        plot(res, a.plot)


if __name__ == "__main__":
    main()
