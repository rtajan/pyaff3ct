#!/usr/bin/env python3
"""A first communication chain: polar code, BPSK modulation, AWGN channel (docs/tutorial/first_chain.md).

The chain is built module by module, run once frame by frame in Python, then as a streampu Sequence until 100 frame
errors are reached.

    python examples/first_chain.py
"""

from __future__ import annotations

import numpy as np
import streampu as spu

import aff3ct as af


def run(ebn0: float = 2.0, max_fe: int = 100) -> dict:
    # --8<-- [start:modules]
    K, N = 96, 128  # information bits, codeword size
    code_rate = K / N

    # frozen bits of the polar code: Gaussian approximation for the noise of the simulation
    noise = af.tools.sigma_from_ebn0(ebn0, code_rate)  # Eb/N0 (dB) -> sigma of the Gaussian noise
    frozen_bits = af.tools.Frozenbits_generator_GA_Arikan(K, N).generate(noise)

    src = af.src.source(K, type="RAND", seed=42)  # random information bits
    enc = af.enc.polar(K, N, frozen_bits)  # polar encoder
    mdm = af.mdm.modem(N, type="BPSK")  # bits -> symbols, symbols -> LLRs
    chn = af.chn.channel(N, type="AWGN", seed=7)  # additive white Gaussian noise
    dec = af.dec.polar(K, N, frozen_bits, type="SC", implem="NAIVE")  # successive cancellation decoder
    mnt = af.mnt.bfer(K, n_frame_errors=max_fe)  # bit and frame error counters
    # --8<-- [end:modules]

    # --8<-- [start:frame]
    sigma = spu.array([noise.sigma], dtype=spu.float32)  # channel parameter, read by the channel and the demodulator

    u = src.generate()[0]  # each call executes the task and returns its output socket(s)
    x = enc.encode(u)
    y = chn.add_noise(sigma, mdm.modulate(x))
    llr = mdm.demodulate(sigma, y)
    cwd, v = dec.decode_siho(llr)  # decode_siho has two outputs: a status (CWD) and the decoded bits (V_K)
    mnt.check_errors(u, v)

    print("sent   ", u.numpy[0, :16])
    print("decoded", v.numpy[0, :16])
    print("bit errors in this frame:", mnt.n_be)
    # --8<-- [end:frame]
    first_frame = {"u": u.numpy.copy(), "v": v.numpy.copy(), "llr": llr.numpy.copy(), "n_be": mnt.n_be}

    # --8<-- [start:sequence]
    # calling the tasks has also bound them together: the chain is a graph that a Sequence executes
    seq = spu.Sequence(mnt["check_errors::status"])  # its first tasks are found from the last socket
    mnt.reset()
    seq.exec()  # until the monitor is done: max_fe frame errors
    print(f"Eb/N0 = {ebn0} dB: {mnt.n_analyzed_frames} frames, FER = {mnt.fer:.3e}, BER = {mnt.ber:.3e}")
    # --8<-- [end:sequence]
    return {"first_frame": first_frame, "fer": mnt.fer, "ber": mnt.ber, "frames": mnt.n_analyzed_frames,
            "n_fe": mnt.n_fe, "K": K, "N": N}


if __name__ == "__main__":
    run()
