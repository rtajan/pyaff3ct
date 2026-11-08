#!/usr/bin/env python3
"""Turbo demodulation (docs/guides/iterative.md): an LDPC code over a GMSK modulation, with an iterative receiver.

The demodulator of a modulation with memory (CPM: GMSK of the GSM standard) and the LDPC decoder exchange soft
information several times on the same frame: a loop of the sequence, built with the ``Switcher`` and the
``Iterator`` of StreamPU, as the ``BFERI`` simulation of AFF3CT. Code: the (4224, 2112) LDPC code of the AFF3CT
references, matrix and interleaver read from the configuration files (lib/aff3ct/conf, fetched by
scripts/fetch_aff3ct_data.sh).

    python examples/turbo_demodulation.py
"""

from __future__ import annotations

from pathlib import Path

import streampu as spu

import aff3ct as af

CONF = Path(__file__).resolve().parent.parent / "lib" / "aff3ct" / "conf"
H_PATH = CONF / "dec" / "LDPC" / "GSM_2112_4224.alist"
ITL_PATH = CONF / "itl" / "GSM-LDPC_4224.itl"


def simulate(ebn0: float, n_ite: int = 10, max_fe: int = 100, n_threads: int = 2) -> af.mnt.Monitor_BFER_AR:
    """BER / FER after ``n_ite`` global iterations (demodulation + one BP iteration of the decoder each)."""
    K, N, upf = 2112, 4224, 5
    # --8<-- [start:modules]
    cdc = af.codec.ldpc(K, N, enc_type="LDPC_H", dec_H_path=str(H_PATH), dec_type="BP_HORIZONTAL_LAYERED",
                        dec_implem="NMS", dec_norm_factor=0.825, dec_n_ite=1)  # one BP iteration per global iteration
    enc, dec = cdc.encoder, cdc.decoder_siso  # decoder_siho is the same decoder (its last decision)
    core = af.tools.interleaver_core(N, type="USER", path=str(ITL_PATH))
    itl_bit, itl_llr1, itl_llr2 = (af.itl.interleaver(core, D=d) for d in (spu.int32, spu.float32, spu.float32))
    mdm_dem = af.mdm.modem(N, type="CPM", cpm_std="GSM", cpm_upf=upf, max="MAX")  # first demodulation
    mdm_ite = af.mdm.modem(N, type="CPM", cpm_std="GSM", cpm_upf=upf, max="MAX")  # demodulation with a priori
    chn = af.chn.channel(mdm_dem.N_mod, type="AWGN", complex=True)
    src = af.src.source(K, type="RAND")
    mnt = af.mnt.Monitor_BFER_AR(K, max_fe)
    swi = spu.Switcher(2, N, spu.float32)  # 2 paths: 0 = one more iteration, 1 = end of the loop
    ite = spu.Iterator(n_ite)  # path 0 n_ite times, then path 1
    # --8<-- [end:modules]
    noise = af.tools.sigma_from_ebn0(ebn0, K / N, upsample_factor=upf)
    sigma = spu.array([noise.sigma], dtype=spu.float32)
    cdc.set_noise(noise)

    # --8<-- [start:loop]
    spu.Task.call_auto_exec = False  # bind only: the loop cannot run before it is closed
    try:
        u = src.generate()[0]
        x = itl_bit.interleave(enc.encode(u))
        y = mdm_dem.filter(sigma, chn.add_noise(sigma, mdm_dem.modulate(x)))
        llr = itl_llr1.deinterleave(mdm_dem.demodulate(sigma, y))  # LLRs of the channel, in the code order
        ite.iterate.bind(swi.select)  # the iterator counts the executions of select
        loop, end = swi.commute(swi["select::out_data"], ite.iterate())
        # one global iteration: decoding, then demodulation with the decoder extrinsic information as a priori
        ext = dec.decode_siso(loop)[1]
        ext = itl_llr2.deinterleave(mdm_ite.tdemodulate(sigma, y, itl_llr2.interleave(ext)))
        swi.select(in_data0=ext, in_data1=llr)  # back to the beginning of the loop (first time: the channel LLRs)
        v = cdc.decoder_siho.decode_siho(end)[1]  # final decision, after the last iteration
        mnt.check_errors(u, v)
    finally:
        spu.Task.call_auto_exec = True
    # --8<-- [end:loop]

    # --8<-- [start:run]
    seq = spu.Sequence(mnt["check_errors::status"], n_threads=n_threads)
    af.tools.seed_sequence(seq)
    af.tools.reset_decoders_on_check(seq)  # the decoder keeps its messages from one iteration to the next
    seq.exec()
    # --8<-- [end:run]
    return mnt


def main() -> None:
    if not H_PATH.exists() or not ITL_PATH.exists():
        raise SystemExit(f"{H_PATH} / {ITL_PATH} missing: run scripts/fetch_aff3ct_data.sh")
    print(" Eb/N0 | iterations |    BER   |    FER")
    for ebn0 in (1.5, 1.75):
        for n_ite in (1, 10):
            mnt = simulate(ebn0, n_ite, max_fe=50)
            print(f" {ebn0:5.2f} | {n_ite:10d} | {mnt.ber:.2e} | {mnt.fer:.2e}")


if __name__ == "__main__":
    main()
