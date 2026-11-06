"""AFF3CT modules inside streampu chains: binding, multi-threaded sequences (clones), exceptions."""

import numpy as np
import pytest
import streampu as spu

import aff3ct as af

K = 32


def _chain():
    src = spu.source_random(K, seed=1, dtype=spu.int32)
    crc = af.factory.CRC(K=K, type="32-GZIP").build()
    v = crc.extract(crc.build(src.generate()[0]))
    return crc, v


@pytest.mark.parametrize("n_threads", [1, 2])
def test_sequence_runs_aff3ct_clones(n_threads):
    _, v = _chain()
    seq = spu.Sequence(v, n_threads=n_threads)
    seq.exec_n_times(20)
    mods = seq.get_modules_per_threads()
    assert len(mods) == n_threads
    for per_thread in mods:
        (crc,) = [m for m in per_thread if m.name.startswith("CRC")]
        assert crc["build::U_K2"].numpy.shape[-1] == K + 32
        np.testing.assert_array_equal(crc["build::U_K1"].numpy, crc["extract::V_K2"].numpy)


def test_modules_returned_by_streampu_keep_their_aff3ct_type():
    # pybind11 types a returned Module* after its dynamic type; an unregistered concrete class (CRC_polynomial_fast)
    # falls back to `Module` unless pystreampu knows how to downcast to the nearest AFF3CT class (registry)
    if not af._ext.HAS_STREAMPU_DOWNCAST_REGISTRY:
        pytest.xfail("this streampu has no Module downcast registry (pyspu::register_module_downcaster)")
    _, v = _chain()
    seq = spu.Sequence(v, n_threads=2)
    for per_thread in seq.get_modules_per_threads():
        (crc,) = [m for m in per_thread if m.name.startswith("CRC")]
        assert isinstance(crc, af.crc.CRC[spu.int32])
        assert (crc.K, crc.size) == (K, 32)


def test_aff3ct_exceptions_are_the_streampu_ones():
    with pytest.raises(spu.exceptions.InvalidArgument, match="NOT-A-POLY"):
        af.factory.CRC(K=64, type="NOT-A-POLY", implem="STD").build()
