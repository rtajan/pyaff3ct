#!/usr/bin/env python3
"""Fixed-point decoding: a polar SC decoder on 8-bit and 16-bit LLRs (docs/guides/fixed_point.md).

Same chains as the AFF3CT references Polar_N128_K96_SC_NO_SYS_p{08,16,32}.txt.

    python examples/fixed_point.py --plot fixed_point.svg
"""

from __future__ import annotations

import argparse

import streampu as spu

import aff3ct as af


def simulate(B, Q, ebn0s, K=96, N=128, max_fe=100, n_threads=2) -> list[float]:
    # --8<-- [start:chain]
    # bits in B (int8, int16 or int32), LLRs of the decoder in Q (int8, int16 or float32); the channel stays in float32
    cdc = af.codec.polar(K, N, enc_systematic=False, dec_type="SC", dec_implem="NAIVE", B=B, Q=Q)
    enc, dec = cdc.encoder, cdc.decoder_siho
    src = af.src.source(K, type="RAND", seed=0, B=B)
    mdm = af.mdm.modem(N, type="BPSK", B=B, R=spu.float32, Q=spu.float32)
    chn = af.chn.channel(N, type="AWGN", seed=1, R=spu.float32)
    mnt = af.mnt.Monitor_BFER_AR(K, max_fe, B=B)
    sigma = spu.array([1.0], dtype=spu.float32)

    u = src.generate()[0]
    llr = mdm.demodulate(sigma, chn.add_noise(sigma, mdm.modulate(enc.encode(u))))
    if Q != spu.float32:
        # fixed point: the LLRs are saturated and quantized on 6 bits, 1 of them after the point (AFF3CT defaults of
        # the polar codes), as the simulator does after the demodulator
        qnt = af.qnt.quantizer(size=N, type="POW2", n_bits=6, n_decimals=1, R=spu.float32, Q=Q)
        llr = qnt.process(llr)
    _, v = dec.decode_siho(llr)
    mnt.check_errors(u, v)
    # --8<-- [end:chain]
    seq = spu.Sequence(mnt["check_errors::status"], n_threads=n_threads)
    fer = []
    for ebn0 in ebn0s:
        noise = af.tools.sigma_from_ebn0(ebn0, K / N)
        sigma.numpy[...] = noise.sigma
        cdc.set_noise(noise)
        seq = spu.Sequence(mnt["check_errors::status"], n_threads=n_threads)  # clones after set_noise
        mnt.reset()
        seq.exec()
        fer.append(mnt.fer)
    return fer


PRECISIONS = {"32 bits (float)": (spu.int32, spu.float32), "16 bits": (spu.int16, spu.int16), "8 bits": (spu.int8, spu.int8)}
REFERENCES = {"32 bits (float)": "p32", "16 bits": "p16", "8 bits": "p08"}


def run(ebn0s=(1.0, 2.0, 3.0), max_fe=100, n_threads=2) -> dict[str, list[float]]:
    return {label: simulate(B, Q, ebn0s, max_fe=max_fe, n_threads=n_threads) for label, (B, Q) in PRECISIONS.items()}


def plot(results, ebn0s, path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    import _references as refs

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for label, fer in results.items():
        line = ax.semilogy(ebn0s, fer, "o", label=f"pyAFF3CT, {label}")
        if refs.available():
            r = refs.read(f"POLAR/AWGN/BPSK/SC/Polar_N128_K96_SC_NO_SYS_{REFERENCES[label]}.txt")
            ax.semilogy(r["ebn0"], r["fer"], "-", color=line[0].get_color(), alpha=0.6, label=f"AFF3CT reference, {label}")
    ax.set_xlabel("Eb/N0 (dB)")
    ax.set_ylabel("Frame error rate")
    ax.set_title("Polar (128, 96), SC decoder, BPSK over AWGN")
    ax.set_xlim(min(ebn0s) - 0.25, max(ebn0s) + 0.25)
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--plot", help="save the curves in this file")
    p.add_argument("--max-fe", type=int, default=100)
    a = p.parse_args()
    ebn0s = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]
    res = run(ebn0s, a.max_fe)
    for label, fer in res.items():
        print(f"{label:16s}", " ".join(f"{f:.2e}" for f in fer))
    if a.plot:
        plot(res, ebn0s, a.plot)
