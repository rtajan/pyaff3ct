#!/usr/bin/env python3
"""SCMA and CPM modulations (docs/guides/modems.md): uncoded bit error rates over an AWGN channel.

SCMA (sparse code multiple access) multiplexes 6 users on 4 resources: one frame per user, the channel sums their
signals. CPM (continuous phase modulation) filters the received signal before the demodulation. The SCMA codebooks
are read from the AFF3CT configuration files (lib/aff3ct/conf, fetched by scripts/fetch_aff3ct_data.sh).

    python examples/scma_cpm.py
"""

from __future__ import annotations

from pathlib import Path

import streampu as spu

import aff3ct as af

CODEBOOK = Path(__file__).resolve().parent.parent / "lib" / "aff3ct" / "conf" / "mod" / "SCMA" / "CS1.cb"


def scma_ber(ebn0: float, K: int = 128, n_frames: int = 1000) -> float:
    # --8<-- [start:scma]
    mdm = af.mdm.modem(K, type="SCMA", codebook_path=str(CODEBOOK), n_ite=6)  # 3 bits per codeword, 6 users
    users = mdm.n_frames  # the modem works on the frames of its 6 users at once
    chn = af.chn.channel(mdm.N_mod, type="AWGN", complex=True, add_users=True)  # sum of the signals of the users
    src = af.src.source(K, type="RAND")
    dec = af.codec.uncoded(K, K).decoder_siho  # hard decision
    mnt = af.mnt.Monitor_BFER_AR(K, 10**9, max_n_frames=n_frames)
    for m in (src, chn, dec, mnt):  # one frame per user in every module, before the bindings
        m.n_frames = users
    sigma = spu.array([af.tools.sigma_from_ebn0(ebn0, bps=3).sigma] * users, dtype=spu.float32)  # per frame
    u = src.generate()[0]
    llr = mdm.demodulate(sigma, chn.add_noise(sigma, mdm.modulate(u)))
    # --8<-- [end:scma]
    mnt.check_errors(u, dec.decode_siho(llr)[1])
    seq = spu.Sequence(mnt["check_errors::status"], n_threads=2)
    af.tools.seed_sequence(seq)
    seq.exec()
    return mnt.ber


def cpm_ber(ebn0: float, K: int = 4003, n_frames: int = 100) -> float:
    # --8<-- [start:cpm]
    upf = 5  # samples per symbol (the default of the GSM standard)
    mdm = af.mdm.modem(K, type="CPM", cpm_std="GSM", cpm_upf=upf, max="MAX")  # GMSK of the GSM standard
    chn = af.chn.channel(mdm.N_mod, type="AWGN", complex=True)
    sigma = spu.array([af.tools.sigma_from_ebn0(ebn0, upsample_factor=upf).sigma], dtype=spu.float32)
    src = af.src.source(K, type="RAND")
    u = src.generate()[0]
    y = chn.add_noise(sigma, mdm.modulate(u))
    llr = mdm.demodulate(sigma, mdm.filter(sigma, y))  # CPM: filtering of the received signal first
    # --8<-- [end:cpm]
    dec = af.codec.uncoded(K, K).decoder_siho
    mnt = af.mnt.Monitor_BFER_AR(K, 10**9, max_n_frames=n_frames)
    mnt.check_errors(u, dec.decode_siho(llr)[1])
    seq = spu.Sequence(mnt["check_errors::status"], n_threads=2)
    af.tools.seed_sequence(seq)
    seq.exec()
    return mnt.ber


if __name__ == "__main__":
    for e in (4.0, 8.0, 12.0):
        print(f"Eb/N0 = {e:4.1f} dB   SCMA BER = {scma_ber(e):.2e}   CPM (GSM) BER = {cpm_ber(e / 2):.2e}")
