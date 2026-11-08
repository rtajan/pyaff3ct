"""Debug tools: Histogram, Frame_trace, Dumper (examples/debugging.py), histogram of Monitor_MI."""

import sys
from pathlib import Path

import numpy as np
import streampu as spu

import aff3ct as af

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "examples"))


def test_example(tmp_path):
    import debugging  # examples/debugging.py

    r = debugging.run(tmp_path)
    assert r["n_fe"] == 10 and {"bad_frames.src", "bad_frames.llr", "llr_histogram.txt"} <= set(r["files"])
    lines = (tmp_path / "bad_frames.src").read_text().split()
    assert int(lines[0]) == 10 and int(lines[1]) == 32  # 10 frames of 32 bits
    assert r["counts"].sum() == 64 and "|" in r["text"]


def test_histogram():
    h = af.tools.Histogram(precision=2)
    assert isinstance(h, af.tools.Histogram[spu.float32])
    h.add_values([0.123, 0.124, 0.5, -1.0])
    x, n = h.values
    np.testing.assert_allclose(x, [-1.0, 0.12, 0.5], atol=1e-6)
    np.testing.assert_array_equal(n, [1, 2, 1])
    assert h.n_values == 4 and h.hist_max == np.float32(0.5)
    h.reset()
    assert h.n_values == 0


def test_frame_trace_returns_text():
    t = af.tools.Frame_trace()
    s = t.display_real_vector(np.array([1.5, -2.0], dtype=np.float32))
    assert "1.5" in s and "-2" in s


def test_mutual_information_histogram():
    N = 256
    src, mdm, chn = af.src.source(N, type="RAND"), af.mdm.modem(N, type="BPSK"), af.chn.channel(N, type="AWGN")
    mnt = af.mnt.mi(N, n_trials=20)
    mnt.activate_mutinfo_histogram(True)
    s = spu.array([0.8], dtype=spu.float32)
    u = src.generate()[0]
    mnt.get_mutual_info(u, mdm.demodulate(s, chn.add_noise(s, mdm.modulate(u))))
    spu.Sequence(mnt["get_mutual_info::status"]).exec()
    assert mnt.mutinfo_hist.n_values == 20
