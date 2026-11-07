#!/usr/bin/env python3
"""BER/FER simulation of an LDPC code (belief propagation) built with a codec, with a multi-threaded Sequence.

Same chain as ``aff3ct -C LDPC -K 64 -N 128 --dec-type BP_HORIZONTAL_LAYERED --dec-implem SPA -i 50
--dec-h-path conf/dec/LDPC/CCSDS_64_128.alist``; reference curve:
``lib/aff3ct/refs/LDPC/AWGN/BPSK/BP_HORIZONTAL_LAYERED/SPA/LDPC_N128_K64_hlayered_SPA_i50_CCSDS.txt``.

    python examples/ldpc_bfer.py path/to/CCSDS_64_128.alist --ebn0 1 4 0.5 --threads 4
"""

from __future__ import annotations

import argparse

import numpy as np
import streampu as spu

import aff3ct as af


def simulate(H_path: str, ebn0s, max_fe=100, n_threads=1, n_ite=50, quiet=False):
    K_N = sorted(af.tools.AList.read_matrix_size(H_path))
    N = K_N[1]
    K = N - K_N[0]
    # encoder computed from H (as the simulator), decoder from the same matrix: one codec builds and connects them
    cdc = af.codec.ldpc(K, N, enc_type="LDPC_H", dec_H_path=H_path, dec_type="BP_HORIZONTAL_LAYERED",
                        dec_implem="SPA", dec_n_ite=n_ite)
    enc, dec = cdc.encoder, cdc.decoder_siho

    src = af.src.source(K, type="RAND", seed=0)
    mdm, chn = af.mdm.modem(N, type="BPSK"), af.chn.channel(N, type="AWGN", seed=1)
    mnt = af.mnt.Monitor_BFER_AR(K, max_fe)
    sigma = spu.array([1.0], dtype=spu.float32)
    u = src.generate()[0]
    dec.decode_siho(mdm.demodulate(sigma, chn.add_noise(sigma, mdm.modulate(enc.encode(u)))))
    mnt.check_errors(u, dec["decode_siho::V_K"])
    seq = spu.Sequence(mnt["check_errors::status"], n_threads=n_threads)

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
        mnt.reset()
        for r in reporters:
            r.init()
        seq.exec()
        if not quiet:
            ter.final_report()
        results.append((ebn0, mnt.ber, mnt.fer, mnt.n_analyzed_frames))
    return results


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("H_path", help="parity-check matrix (AList or QC file)")
    p.add_argument("--ebn0", type=float, nargs=3, default=(1.0, 4.0, 0.5), metavar=("MIN", "MAX", "STEP"))
    p.add_argument("--max-fe", type=int, default=100)
    p.add_argument("--threads", type=int, default=1)
    p.add_argument("--ite", type=int, default=50)
    a = p.parse_args()
    ebn0s = np.arange(a.ebn0[0], a.ebn0[1] + 1e-9, a.ebn0[2]).round(4).tolist()
    simulate(a.H_path, ebn0s, a.max_fe, a.threads, a.ite)


if __name__ == "__main__":
    main()
