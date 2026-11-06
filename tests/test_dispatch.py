"""Choice of the C++ instance from the pystreampu dtypes (Plan.md, rule R3)."""

import pytest
import streampu as spu

import aff3ct as af
from aff3ct._dispatch import Template


def test_templates_are_exported():
    for tpl in (af.enc.Encoder, af.crc.CRC, af.chn.Channel, af.mdm.Modem, af.qnt.Quantizer, af.dec.Decoder_SIHO):
        assert isinstance(tpl, Template)
    # non-template classes are exported as is
    assert isinstance(af.dec.Decoder, type)
    assert isinstance(af.mnt.Monitor, type)


def test_instances_are_named_after_the_pystreampu_dtypes():
    assert af.enc.Encoder[spu.int16].__name__ == "Encoder_int16"
    assert af.dec.Decoder_SIHO[spu.int32, spu.float32].__name__ == "Decoder_SIHO_int32_float32"
    assert set(af.enc.Encoder.instances) == {("int8",), ("int16",), ("int32",), ("int64",)}


def test_defaults_are_the_32_bit_precision():
    assert af.enc.Encoder.resolve() is af.enc.Encoder[spu.int32]
    assert af.dec.Decoder_SIHO.resolve() is af.dec.Decoder_SIHO[spu.int32, spu.float32]
    # C++ default Q = int is not compiled: Q = float32 (Q_32)
    assert af.qnt.Quantizer.resolve().__name__ == "Quantizer_float32_float32"
    # Q = R in the C++ template
    assert af.mdm.Modem.resolve().__name__ == "Modem_int32_float32_float32"


def test_missing_parameter_takes_the_only_compatible_value():
    assert af.dec.Decoder_SIHO.resolve(B=spu.int8).__name__ == "Decoder_SIHO_int8_int8"
    assert af.dec.Decoder_SIHO.resolve(B=spu.int64).__name__ == "Decoder_SIHO_int64_float64"
    # several compatible values: the default breaks the tie (Q = R = float32)
    assert af.mdm.Modem.resolve(B=spu.int8).__name__ == "Modem_int8_float32_float32"
    assert af.mdm.Modem.resolve(B=spu.int8, Q=spu.int8).__name__ == "Modem_int8_float32_int8"


def test_dtype_keyword_for_single_parameter_templates():
    assert af.enc.Encoder.resolve(dtype=spu.int64) is af.enc.Encoder[spu.int64]
    with pytest.raises(TypeError, match="several template parameters"):
        af.dec.Decoder_SIHO.resolve(dtype=spu.int32)


@pytest.mark.parametrize("dt", [spu.uint8, spu.uint16, spu.uint32, spu.uint64])
def test_unsigned_dtypes_are_rejected(dt):
    with pytest.raises(TypeError, match="not compiled for .*Available"):
        af.enc.Encoder.resolve(B=dt)


def test_errors():
    with pytest.raises(TypeError, match="not compiled for"):
        af.dec.Decoder_SIHO.resolve(B=spu.int8, R=spu.float32)
    with pytest.raises(TypeError, match="unknown template parameter"):
        af.enc.Encoder.resolve(R=spu.float32)
    with pytest.raises(TypeError, match="must be a streampu dtype"):
        af.enc.Encoder.resolve(B="int32")
    with pytest.raises(TypeError, match="give the template parameter 'D'"):
        af.cst.Coset.resolve()  # D has no default and several compatible values


def test_isinstance_and_issubclass_on_templates():
    assert issubclass(af.enc.Encoder[spu.int8], af.enc.Encoder)
    assert not issubclass(af.dec.Decoder_SIHO[spu.int8, spu.int8], af.enc.Encoder)
    assert issubclass(af.dec.Decoder_SISO[spu.int32, spu.float32], af.dec.Decoder_SIHO)
