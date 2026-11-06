"""Automatic conversions (Plan.md, rule R7) and noise tools."""

import numpy as np
import pytest
import streampu as spu

import aff3ct as af

T = af._ext._testing


def test_bool_vector_from_numpy_and_lists():
    fb = np.array([True, False, True, True])
    out = T.bool_vector_roundtrip(fb)
    assert isinstance(out, np.ndarray) and out.dtype == np.bool_
    np.testing.assert_array_equal(out, fb)
    np.testing.assert_array_equal(T.bool_vector_roundtrip([1, 0, 0]), [True, False, False])
    np.testing.assert_array_equal(T.bool_vector_roundtrip(np.array([0, 2, 0], dtype=np.int32)), [False, True, False])
    assert T.bool_vector_size(np.zeros(1024, dtype=bool)) == 1024
    assert T.bool_vector_roundtrip([]).size == 0


@pytest.mark.parametrize("bad", ["0101", [[True, False]], None])
def test_bool_vector_rejects_invalid_inputs(bad):
    with pytest.raises(TypeError):
        T.bool_vector_roundtrip(bad)


def test_noise_sigma():
    s = af.tools.Sigma[spu.float32](0.5)
    assert isinstance(s, af.tools.Noise) and isinstance(s, af.tools.Sigma)
    assert s.value == pytest.approx(0.5) and float(s) == pytest.approx(0.5)
    assert s.type == af.tools.Noise_type.SIGMA and s.is_set()
    s.set_values(0.7, 3.0, 3.0)
    assert (s.sigma, s.ebn0, s.esn0) == pytest.approx((0.7, 3.0, 3.0))
    assert repr(s).startswith("SIGMA(")
    assert not af.tools.Sigma[spu.float64]().is_set()


def test_noise_event_probability():
    ep = af.tools.Event_probability.resolve(R=spu.float64)(0.1)
    assert ep.type == af.tools.Noise_type.EP and ep.value == pytest.approx(0.1)
    ep.set_value(0.2)
    assert ep.value == pytest.approx(0.2)
