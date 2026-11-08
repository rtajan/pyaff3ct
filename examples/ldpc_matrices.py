#!/usr/bin/env python3
"""LDPC matrices: Sparse_matrix, AList files, generator matrices, decoders from a matrix (docs/guides/ldpc.md).

    python examples/ldpc_matrices.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import streampu as spu

import aff3ct as af


def run() -> dict:
    # --8<-- [start:matrix]
    # parity-check matrix of the Hamming (7, 4) code, from any 2D array (non-zero = one)
    H = af.tools.Sparse_matrix(np.array([[1, 1, 0, 1, 1, 0, 0],
                                         [1, 0, 1, 1, 0, 1, 0],
                                         [0, 1, 1, 1, 0, 0, 1]]))
    print(H, H.shape, H.n_connections)
    print(H.to_dense())  # numpy.ndarray[uint8]; H.to_scipy() gives a scipy.sparse matrix
    print(H.row_to_cols)  # positions of the ones of each row
    # --8<-- [end:matrix]

    # --8<-- [start:alist]
    path = Path(tempfile.mkdtemp()) / "hamming.alist"
    af.tools.AList.write(H, path)
    H2 = af.tools.AList.read(path)
    print(H2.shape, H2 == H)
    # --8<-- [end:alist]

    # --8<-- [start:generator]
    G, info_bits_pos = af.tools.LDPC_matrix_handler.transform_H_to_G(H)  # Gaussian elimination
    print(info_bits_pos, af.tools.LDPC_matrix_handler.check_GH(H, G))
    # --8<-- [end:generator]

    # --8<-- [start:modules]
    K, N = 4, 7
    # the LDPC modules take H vertically (N rows, one column per parity check), as the AList files of AFF3CT
    Hv = H.turn(af.tools.Matrix.Way.VERTICAL)
    enc = af.enc.ldpc(K, N, af.tools.Sparse_matrix(), Hv, type="LDPC_H")  # G computed by the encoder from H
    dec = af.dec.ldpc(K, N, Hv, enc.info_bits_pos, type="BP_FLOODING", implem="SPA", n_ite=10)
    u = spu.array([1, 0, 1, 1], dtype=spu.int32)
    x = enc.encode(u)
    llr = spu.array((4.0 * (1 - 2 * x.numpy[0])).tolist(), dtype=spu.float32)  # noiseless LLRs
    llr.numpy[0, 2] *= -1  # one wrong bit...
    _, v = dec.decode_siho(llr)
    print(v.numpy, u.numpy)  # ...corrected
    # --8<-- [end:modules]
    return {"H": H, "H2": H2, "G": G, "info_bits_pos": info_bits_pos, "u": u.numpy.copy(), "v": v.numpy.copy()}


if __name__ == "__main__":
    run()
