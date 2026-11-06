"""Factories: keyword parameters, command-line parity, builders dispatched on the dtypes (Plan.md, rule R5).

The CRC factory is the test bed of the phase 1: it builds real modules whose tasks run through pystreampu.
"""

import numpy as np
import pytest
import streampu as spu

import aff3ct as af
from aff3ct import _factory


def test_keyword_parameters_and_repr():
    f = af.factory.CRC(K=64, type="32-GZIP", implem="STD")
    assert (f.K, f.type, f.implem) == (64, "32-GZIP", "STD")
    assert f.parameters == {"K": 64, "type": "32-GZIP", "implem": "STD", "size": 0}
    assert repr(f) == "CRC(K=64, type='32-GZIP', implem='STD', size=0)"
    assert f.prefix == "crc"


def test_unknown_parameter_lists_the_valid_ones():
    with pytest.raises(TypeError, match=r"unknown parameter\(s\) \['poly'\].*valid parameters: \['K', 'type'"):
        af.factory.CRC(poly="32-GZIP")


def test_from_cli_on_the_class_and_on_an_instance():
    f = af.factory.CRC.from_cli("--crc-type 32-GZIP --crc-implem STD", K=64)
    assert isinstance(f, af.factory.CRC)
    # the AFF3CT parsing (`store()`) also computes the derived values: the CRC size comes from the polynomial
    assert f.parameters == {"K": 64, "type": "32-GZIP", "implem": "STD", "size": 32}
    # an instance is updated in place (only the given arguments change)
    assert f.from_cli(["--crc-implem", "FAST"]) is f
    assert (f.type, f.implem) == ("32-GZIP", "FAST")


def test_keywords_and_command_line_build_the_same_module():
    kw = af.factory.CRC(K=64, type="32-GZIP", implem="STD")
    cl = af.factory.CRC.from_cli("--crc-type 32-GZIP --crc-implem STD", K=64)
    assert kw.size == 0  # user value kept (0 = deduced): the derived values are computed at build time
    a, b = kw.build(), cl.build()
    assert type(a) is type(b) and (a.K, a.size) == (b.K, b.size) == (64, 32)


def test_derived_values_follow_the_parameters():
    f = af.factory.CRC(K=64, type="32-GZIP")
    assert f.build().size == 32
    f.type = "8-DVB-S2"  # the size derived from the previous polynomial must not be reused
    assert f.build().size == 8


def test_from_cli_errors():
    with pytest.raises(ValueError, match="invalid AFF3CT arguments"):
        af.factory.CRC.from_cli("--crc-implem WRONG")
    with pytest.raises(ValueError, match="Unknown argument"):
        af.factory.CRC.from_cli("--enc-type POLAR")  # argument of another factory


def test_headers():
    h = af.factory.CRC(K=64, type="32-GZIP").headers()
    assert isinstance(h, dict) and h
    values = {k: v for section in h.values() for k, v in section.items()}
    assert "32-GZIP" in values.values()


def test_clone():
    f = af.factory.CRC(K=64, type="32-GZIP")
    g = f.clone()
    g.K = 128
    assert (f.K, g.K) == (64, 128) and isinstance(g, af.factory.CRC)


@pytest.mark.parametrize("dt", [spu.int8, spu.int16, spu.int32, spu.int64])
def test_build_dispatches_on_the_dtypes(dt):
    crc = af.factory.CRC(K=64, type="32-GZIP").build(B=dt)
    assert isinstance(crc, af.crc.CRC)
    assert type(crc) is af.crc.CRC[dt] or issubclass(type(crc), af.crc.CRC[dt])
    assert (crc.K, crc.size) == (64, 32)


def test_build_defaults_and_errors():
    assert isinstance(af.factory.CRC(K=8, type="8-DVB-S2").build(), af.crc.CRC[spu.int32])
    with pytest.raises(TypeError, match="not compiled for"):
        af.factory.CRC(K=8, type="8-DVB-S2").build(B=spu.uint8)


def test_transparent_build_engine():
    # what the module-level functions do: the factory is a temporary, only the module is returned
    crc = _factory.build(af.factory.CRC, {"K": 16, "type": "16-CCITT", "implem": None}, {"B": spu.int16})
    assert isinstance(crc, af.crc.CRC[spu.int16]) and (crc.K, crc.size) == (16, 16)


def test_built_module_runs_through_streampu():
    K = 32
    crc = af.factory.CRC(K=K, type="32-GZIP").build(B=spu.int32)
    rng = np.random.default_rng(0)
    u = spu.array(rng.integers(0, 2, K).tolist(), dtype=spu.int32)

    x = crc.build(u)  # task `build` (U_K1 -> U_K2): information bits + CRC
    assert x.numpy.shape[-1] == K + 32
    np.testing.assert_array_equal(x.numpy[..., :K], u.numpy)

    v = crc.extract(x)  # task `extract` (V_K1 -> V_K2)
    np.testing.assert_array_equal(v.numpy, u.numpy)
    assert crc["build::U_K2"].numpy.shape[-1] == K + 32
