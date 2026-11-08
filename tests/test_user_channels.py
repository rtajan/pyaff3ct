"""Channels whose noise, erasures, flips or gains are read from a file (types USER, USER_ADD, USER_BEC, USER_BSC,
RAYLEIGH_USER): text files "n_frames frame_size values..." (RAYLEIGH_USER: a list of gains)."""

import numpy as np
import streampu as spu

import aff3ct as af

N = 8


def write_frames(path, frames):
    frames = np.asarray(frames, dtype=float)
    path.write_text(f"{frames.shape[0]} {frames.shape[1]}\n" + "\n".join(" ".join(map(str, f)) for f in frames))
    return str(path)


def run(chn, x, with_gains=False):
    cp = spu.array([0.0], dtype=spu.float32)
    xs = spu.array(np.asarray(x, dtype=np.float32), dtype=spu.float32)
    if with_gains:
        h, y = chn.add_noise_wg(cp, xs)
        return h.numpy[0].copy(), y.numpy[0].copy()
    return chn.add_noise(cp, xs).numpy[0].copy()


def test_user_received_samples(tmp_path):
    frames = np.arange(2 * N).reshape(2, N) / 10
    chn = af.chn.channel(N, type="USER", path=write_frames(tmp_path / "rx.txt", frames))
    x = np.ones(N)
    np.testing.assert_allclose(run(chn, x), frames[0], rtol=1e-6)  # the received samples are those of the file
    np.testing.assert_allclose(run(chn, x), frames[1], rtol=1e-6)  # frame after frame
    np.testing.assert_allclose(run(chn, x), frames[0], rtol=1e-6)  # cyclically


def test_user_additive_noise(tmp_path):
    noise = np.linspace(-1, 1, N)[None, :]
    chn = af.chn.channel(N, type="USER_ADD", path=write_frames(tmp_path / "noise.txt", noise))
    x = np.arange(N, dtype=float)
    np.testing.assert_allclose(run(chn, x), x + noise[0], rtol=1e-6)


def test_user_erasures_and_flips(tmp_path):
    events = np.array([[1, 0, 0, 1, 0, 0, 0, 1]])
    x = np.array([0, 1, 0, 1, 1, 0, 1, 0], dtype=float)  # OOK symbols
    bec = af.chn.channel(N, type="USER_BEC", path=write_frames(tmp_path / "erasures.txt", events))
    y = run(bec, x)
    np.testing.assert_array_equal(y[events[0] == 0], x[events[0] == 0])  # kept
    assert (y[events[0] == 1] != x[events[0] == 1]).all()  # erased (unknown value)
    bsc = af.chn.channel(N, type="USER_BSC", path=write_frames(tmp_path / "flips.txt", events))
    np.testing.assert_array_equal(run(bsc, x), np.where(events[0] == 1, 1 - x, x))  # flipped where an event


def test_rayleigh_user_gains(tmp_path):
    gains = np.linspace(0.5, 2.0, N)
    path = tmp_path / "gains.txt"
    path.write_text(" ".join(map(str, gains)))
    chn = af.chn.channel(N, type="RAYLEIGH_USER", path=str(path), gain_occur=1)
    x = np.ones(N)
    h, y = run(chn, x, with_gains=True)  # no noise (sigma = 0): the received samples are the gains
    np.testing.assert_allclose(h, gains, rtol=1e-6)
    np.testing.assert_allclose(y, gains, rtol=1e-6)
