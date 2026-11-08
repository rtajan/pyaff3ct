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


def test_constellation_from_symbols():
    c = af.tools.Constellation([2, 2j, -2, -2j])
    assert isinstance(c, af.tools.Constellation[spu.float32]) and c.bps == 2 and c.is_complex()
    np.testing.assert_allclose(c.symbols, [1, 1j, -1, -1j], atol=1e-6)  # unit mean energy
    np.testing.assert_allclose(af.tools.Constellation([2, -2], normalize=False).symbols, [2, -2])
    with pytest.raises(Exception, match="power of 2"):
        af.tools.Constellation([1, 2, 3])


@pytest.mark.parametrize("type_", [None, "USER"])
def test_modem_from_symbols(type_):
    K = 99
    psk8 = np.exp(2j * np.pi * np.arange(8) / 8)
    kw = {} if type_ is None else {"type": type_}
    mdm = af.mdm.modem(K, symbols=psk8, **kw)
    gc.collect()
    assert mdm.N_mod == 2 * 33
    u = spu.array(np.random.default_rng(2).integers(0, 2, K).tolist(), dtype=spu.int32)
    x = mdm.modulate(u)
    sym = x.numpy[0][0::2] + 1j * x.numpy[0][1::2]
    bits = u.numpy[0].reshape(-1, 3) @ np.array([1, 2, 4])
    np.testing.assert_allclose(sym, psk8[bits], atol=1e-5)  # symbol i = image of the bits of i, LSB first
    llr = mdm.demodulate(spu.array([0.01], dtype=spu.float32), x)
    np.testing.assert_array_equal((llr.numpy[0] < 0).astype(np.int32), u.numpy[0])
    assert "symbols" in __import__("inspect").signature(af.mdm.modem).parameters
    with pytest.raises(TypeError, match="either"):
        af.mdm.modem(K, af.tools.Constellation_PSK(3), symbols=psk8)


@pytest.mark.parametrize("bit_order, weights", [("LSB", [1, 2, 4]), ("MSB", [4, 2, 1])])
def test_modem_bit_order(bit_order, weights):
    K = 99
    psk8 = np.exp(2j * np.pi * np.arange(8) / 8)
    mdm = af.mdm.modem(K, symbols=psk8, bit_order=bit_order)
    u = spu.array(np.random.default_rng(3).integers(0, 2, K).tolist(), dtype=spu.int32)
    x = mdm.modulate(u)
    sym = x.numpy[0][0::2] + 1j * x.numpy[0][1::2]
    np.testing.assert_allclose(sym, psk8[u.numpy[0].reshape(-1, 3) @ np.array(weights)], atol=1e-5)
    llr = mdm.demodulate(spu.array([0.01], dtype=spu.float32), x)
    np.testing.assert_array_equal((llr.numpy[0] < 0).astype(np.int32), u.numpy[0])


def test_modem_bit_order_errors():
    with pytest.raises(ValueError, match="bit_order"):
        af.mdm.modem(8, symbols=[1, -1], bit_order="msb")
    with pytest.raises(TypeError, match="symbols"):
        af.mdm.modem(8, type="QAM", bps=2, bit_order="MSB")
