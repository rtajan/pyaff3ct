#!/usr/bin/env python3
"""Polar codes: frozen bits, decoders, CRC-aided list decoding, frozen bits of the clones (docs/guides/polar.md).

    python examples/polar_codes.py
"""

from __future__ import annotations

import numpy as np
import streampu as spu

import aff3ct as af


def frozen_bits_demo(K=16, N=32) -> dict:
    # --8<-- [start:frozen_bits]
    # Gaussian approximation (Arikan kernel): the reliability of the bit channels depends on the noise
    gen = af.tools.Frozenbits_generator_GA_Arikan(K, N)
    frozen_bits = gen.generate(af.tools.sigma_from_ebn0(1.0, K / N))  # numpy.ndarray[bool], True = frozen
    print("frozen bits:", frozen_bits.astype(int))
    print("bit channels, most reliable first:", gen.best_channels)

    # other constructions: Reed-Muller (independent of the noise), 5G sequence, files...
    fb_rm = af.tools.Frozenbits_generator_RM(K, N).generate()
    # --8<-- [end:frozen_bits]
    return {"frozen_bits": frozen_bits, "fb_rm": fb_rm, "best": gen.best_channels}


def decoders_demo(K=32, N=64, ebn0=2.0) -> dict:
    noise = af.tools.sigma_from_ebn0(ebn0, K / N)
    fb = af.tools.Frozenbits_generator_GA_Arikan(K, N).generate(noise)
    # --8<-- [start:decoders]
    enc = af.enc.polar(K, N, fb)  # systematic by default (AFF3CT default)
    sc = af.dec.polar(K, N, fb, type="SC", implem="NAIVE")
    scl = af.dec.polar(K, N, fb, type="SCL", implem="NAIVE", L=8)
    print(type(sc).__name__, sc.frozen_bits.sum(), "frozen bits")  # interface of the polar decoders
    sc.set_frozen_bits(fb)  # the frozen bits can be changed after the construction
    print(hasattr(af.dec.repetition(K, 3 * K), "frozen_bits"))  # False: no frozen bits for the other codes
    # --8<-- [end:decoders]

    # --8<-- [start:ca_scl]
    # CRC-aided SCL: the CRC chooses among the L candidates (the K bits of the code include the CRC)
    crc = af.crc.crc(K - 8, type="8-DVB-S2")
    ca_scl = af.dec.polar(K, N, fb, crc, type="SCL", implem="NAIVE", L=8)
    # --8<-- [end:ca_scl]
    return {"enc": enc, "sc": sc, "scl": scl, "ca_scl": ca_scl, "crc": crc, "fb": fb}


def clones_demo(K=32, N=64, n_threads=2) -> dict:
    # --8<-- [start:clones]
    cdc = af.codec.polar(K, N, dec_type="SC", dec_implem="NAIVE")  # frozen bits adapted to the noise
    src, mdm = af.src.source(K, seed=0), af.mdm.modem(N)
    chn, mnt = af.chn.channel(N, seed=1), af.mnt.Monitor_BFER_AR(K, 50)
    sigma = spu.array([1.0], dtype=spu.float32)
    u = src.generate()[0]
    _, v = cdc.decoder_siho.decode_siho(mdm.demodulate(sigma, chn.add_noise(sigma, mdm.modulate(cdc.encoder.encode(u)))))
    mnt.check_errors(u, v)

    fers = []
    for ebn0 in (1.0, 3.0):
        noise = af.tools.sigma_from_ebn0(ebn0, K / N)
        sigma.numpy[...] = noise.sigma
        cdc.set_noise(noise)  # new frozen bits for the encoder and the decoder of the codec...
        # ...but not for the clones of an existing Sequence: build it after set_noise, or update the clones with
        # seq.get_cloned_modules(cdc.encoder) / (cdc.decoder_siho) and their set_frozen_bits
        seq = spu.Sequence(mnt["check_errors::status"], n_threads=n_threads)
        af.tools.seed_sequence(seq)  # each thread its own frames and noise
        mnt.reset()
        seq.exec()
        fers.append(mnt.fer)
    # --8<-- [end:clones]
    print("FER at 1 dB and 3 dB:", fers)
    return {"fers": fers}


def run() -> dict:
    return {"frozen": frozen_bits_demo(), "decoders": decoders_demo(), "clones": clones_demo()}


if __name__ == "__main__":
    run()
