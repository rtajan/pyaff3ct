"""Constellations and generic modems (aff3ct.tools.Constellation_*, aff3ct.mdm.modem)."""

import gc

import numpy as np
import pytest
import streampu as spu

import aff3ct as af


@pytest.mark.parametrize(
    "cls, bps, complex_",
    [("Constellation_QAM", 4, True), ("Constellation_PSK", 3, True), ("Constellation_PAM", 2, False)],
)
def test_constellations(cls, bps, complex_):
    c = getattr(af.tools, cls)(bps)
    assert isinstance(c, af.tools.Constellation[spu.float32])
    assert (c.bps, c.n_symbols, len(c), c.is_complex()) == (bps, 2**bps, 2**bps, complex_)
    s = c.symbols
    assert s.dtype == np.complex64 and np.mean(np.abs(s) ** 2) == pytest.approx(1.0, rel=1e-5)
    assert c[0] == s[0] and c[-1] == s[-1]
    with pytest.raises(IndexError):
        c[2**bps]


def test_user_constellation(tmp_path):
    path = tmp_path / "c.txt"
    path.write_text("1 0\n0 1\n-1 0\n0 -1\n")
    c = af.tools.Constellation_user(str(path))
    assert c.bps == 2 and np.allclose(c.symbols, [1, 1j, -1, -1j])


def test_generic_modem_builds_its_constellation():
    K = 100
    mdm = af.mdm.modem(K, type="QAM", bps=4)
    assert isinstance(mdm, af.mdm.Modem) and (mdm.N, mdm.N_mod) == (K, 2 * 25)
    gc.collect()  # the constellation built for the modem is kept alive by it
    u = spu.array(np.random.default_rng(0).integers(0, 2, K).tolist(), dtype=spu.int32)
    x = mdm.modulate(u)
    sig = spu.array([0.01], dtype=spu.float32)
    llr = mdm.demodulate(sig, x)
    np.testing.assert_array_equal((llr.numpy[0] < 0).astype(np.int32), u.numpy[0])


def test_modem_with_a_given_constellation():
    mdm = af.mdm.modem(30, af.tools.Constellation_PSK(3))
    gc.collect()
    assert mdm.N_mod == 2 * 10
    assert "constellation is built" in af.mdm.modem.__doc__
