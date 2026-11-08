#!/usr/bin/env python3
"""Debug tools (docs/guides/debugging.md): text view of frames, recording of the frames in error, histograms.

    python examples/debugging.py [output_dir]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import streampu as spu

import aff3ct as af


def run(out: Path, K: int = 32, N: int = 64, ebn0: float = 1.0) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    src = af.src.source(K, type="RAND")
    enc = af.enc.repetition(K, N)
    mdm, chn = af.mdm.modem(N, type="BPSK"), af.chn.channel(N, type="AWGN")
    dec = af.dec.repetition(K, N)
    mnt = af.mnt.bfer(K, n_frame_errors=10)
    sigma = spu.array([af.tools.sigma_from_ebn0(ebn0, K / N).sigma], dtype=spu.float32)
    u = src.generate()[0]
    llr = mdm.demodulate(sigma, chn.add_noise(sigma, mdm.modulate(enc.encode(u))))
    _, v = dec.decode_siho(llr)
    mnt.check_errors(u, v)

    # --8<-- [start:trace]
    trace = af.tools.Frame_trace(n_bits=16)  # the first 16 values of a frame
    text = trace.display_bit_vector(v.numpy[0], ref=u.numpy[0])  # the decoded bits, compared with the sent ones
    print(text)
    # --8<-- [end:trace]

    # --8<-- [start:dumper]
    dumper = af.tools.Dumper()
    dumper.register_data(u, file_ext="src")  # the sockets to record (read at each add)
    dumper.register_data(llr, file_ext="llr")
    mnt.record_callback_fe(lambda n_bit_errors, frame_id: dumper.add(n_bit_errors, frame_id))  # at each frame error
    mnt.reset()  # the frames of the first (binding) execution are not recorded: start counting now
    spu.Sequence(mnt["check_errors::status"]).exec()  # one thread: the callback runs in it
    dumper.dump(str(out / "bad_frames"))  # bad_frames.src, bad_frames.llr: the 10 frames in error
    # --8<-- [end:dumper]

    # --8<-- [start:histogram]
    hist = af.tools.Histogram(precision=1)  # values rounded to 0.1
    hist.add_values(llr.numpy)
    x, counts = hist.values  # the rounded LLRs and their counts
    hist.dump(str(out / "llr_histogram.txt"))
    # --8<-- [end:histogram]
    return {"text": text, "n_fe": mnt.n_fe, "files": sorted(p.name for p in out.iterdir()), "x": x,
            "counts": counts}


if __name__ == "__main__":
    r = run(Path(sys.argv[1] if len(sys.argv) > 1 else "debug_output"))
    print(r["files"], f"{len(r['x'])} histogram bins")
