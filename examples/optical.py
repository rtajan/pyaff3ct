#!/usr/bin/env python3
"""Optical channel: OOK modulation, noise given by measured distributions of the received values for each received
optical power (ROP) (docs/guides/modems.md). The distributions are read from the AFF3CT configuration files
(lib/aff3ct/conf/chn/optical_channel.dist, fetched by scripts/fetch_aff3ct_data.sh).

    python examples/optical.py
"""

from __future__ import annotations

from pathlib import Path

import streampu as spu

import aff3ct as af

PDF = Path(__file__).resolve().parent.parent / "lib" / "aff3ct" / "conf" / "chn" / "optical_channel.dist"


def uncoded_ber(rops, K: int = 4096, n_frames: int = 200) -> list[float]:
    # --8<-- [start:optical]
    dist = af.tools.Distributions(str(PDF))  # densities of the received values, for the ROPs of dist.noise_range
    mdm = af.mdm.modem(K, None, dist, type="OOK", channel_type="OPTICAL")  # demodulation with the densities
    chn = af.chn.channel(K, dist, type="OPTICAL")
    rop = spu.array([rops[0]], dtype=spu.float32)  # the noise of the optical channel: the ROP (dB)
    for r in rops:  # the densities of the simulated ROPs, before the first execution
        dist.read_distribution(r)
    src = af.src.source(K, type="RAND")
    u = src.generate()[0]
    llr = mdm.demodulate(rop, chn.add_noise(rop, mdm.modulate(u)))
    # --8<-- [end:optical]
    dec = af.codec.uncoded(K, K).decoder_siho
    mnt = af.mnt.Monitor_BFER_AR(K, 10**9, max_n_frames=n_frames)
    mnt.check_errors(u, dec.decode_siho(llr)[1])
    seq = spu.Sequence(mnt["check_errors::status"], n_threads=2)
    af.tools.seed_sequence(seq)
    out = []
    for r in rops:
        rop.numpy[...] = r
        mnt.reset()
        seq.exec()
        out.append(mnt.ber)
    return out


if __name__ == "__main__":
    rops = [float(r) for r in af.tools.Distributions(str(PDF)).noise_range[::5]]  # ROPs of the file (dB)
    for r, ber in zip(rops, uncoded_ber(rops)):
        print(f"ROP = {r:6.1f} dB   BER = {ber:.2e}")
