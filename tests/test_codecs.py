"""Codecs (aff3ct.codec): functions built at import from the codec factories, prefixed sub-factory parameters."""

import inspect

import numpy as np
import pytest
import streampu as spu

import aff3ct as af
from aff3ct._generated.functions import CODECS


def llr_of(x):
    return spu.array((4.0 * (1.0 - 2.0 * np.asarray(x.numpy[0], dtype=np.float32))).tolist(), dtype=spu.float32)


def test_one_function_per_codec_family():
    assert {i["function"] for i in CODECS.values()} == set(af.codec.FUNCTIONS)
    assert {"polar", "ldpc", "turbo", "bch", "rs", "rsc", "ra", "repetition", "uncoded"} <= set(af.codec.FUNCTIONS)
    assert isinstance(af.codec.Codec_polar, af._dispatch.Template)


def test_signature_prefixed_parameters():
    sig = inspect.signature(af.codec.polar)
    params = sig.parameters
    P = inspect.Parameter
    assert [n for n, p in params.items() if p.kind == P.POSITIONAL_OR_KEYWORD] == ["K", "N_cw", "crc"]
    assert {"N", "dec_type", "dec_L", "enc_systematic", "fbg_type", "fbg_noise", "pct_type", "B", "Q"} <= set(params)
    assert all(p.kind == P.KEYWORD_ONLY for n, p in params.items() if n not in ("K", "N_cw", "crc"))
    assert "enc_K" not in params and "dec_N_cw" not in params  # sizes: K, N_cw (and N)
    # sub-factories that share their command-line prefix are set together: --enc-sub-* -> enc_sub_*
    turbo = inspect.signature(af.codec.turbo).parameters
    assert {"enc_sub_standard", "dec_sub_max", "dec_sf_type", "itl_core_type"} <= set(turbo)
    assert "enc_sub1_standard" not in turbo
    assert "dec.sub1" in af.codec.turbo.__doc__ and "dec.sub2" in af.codec.turbo.__doc__


def test_polar_codec_modules():
    K, N = 32, 64
    cdc = af.codec.polar(K, N, dec_type="SC", dec_implem="NAIVE", fbg_noise=0.8)
    assert isinstance(cdc, af.codec.Codec_polar[spu.int32, spu.float32])
    assert isinstance(cdc, af.codec.Codec_SISO) and isinstance(cdc, af.interfaces.Interface_get_set_frozen_bits)
    enc, dec = cdc.encoder, cdc.decoder_siho
    assert isinstance(enc, af.enc.Encoder) and isinstance(dec, af.dec.Decoder_SIHO)
    assert cdc.decoder_siso is None and cdc.interleaver is None  # SC: no SISO decoder
    assert isinstance(af.codec.polar(K, N, dec_type="SCAN", dec_implem="NAIVE", fbg_noise=0.8).decoder_siso,
                      af.dec.Decoder_SISO)
    assert cdc.frozen_bits.sum() == N - K
    np.testing.assert_array_equal(enc.frozen_bits, cdc.frozen_bits)
    u = spu.array(np.random.default_rng(0).integers(0, 2, K).tolist(), dtype=spu.int32)
    dec.decode_siho(llr_of(enc.encode(u)))
    np.testing.assert_array_equal(dec["decode_siho::V_K"].numpy, u.numpy)


def test_codec_dtypes_and_factory():
    cdc = af.codec.repetition(8, 24, B=spu.int16)
    assert isinstance(cdc, af.codec.Codec_repetition[spu.int16, spu.int16])
    f = af.codec.polar.factory(32, 64, dec_type="SCL", dec_L=4)
    assert isinstance(f, af.factory.Codec_polar) and (f.dec.type, f.dec.L, f.K, f.N_cw) == ("SCL", 4, 32, 64)
    assert f.headers()["dec"]["Type (D)"] == "SCL"


def test_puncturer_from_N():
    cdc = af.codec.polar(48, 64, N=60, fbg_noise=0.8)
    pct = cdc.puncturer
    assert (pct.K, pct.N, pct.N_cw) == (48, 60, 64)
    with pytest.raises(TypeError, match="no puncturer"):
        af.codec.bch(106, 127, N=120)


@pytest.mark.parametrize(
    "name, K, N, kw",
    [
        ("repetition", 8, 24, {}),
        ("uncoded", 8, 8, {}),
        ("rsc", 16, 38, {}),
        ("conv", 16, 44, {}),
        ("turbo", 40, 132, {"dec_n_ite": 4}),
        ("ra", 16, 48, {}),
        ("bch", 106, 127, {}),
        ("rs", 11, 15, {}),  # sizes in symbols
        ("polar_mk", 64, 128, {}),
        ("turbo_product", 11, 15, {}),  # sizes of the BCH sub-code
    ],
)
def test_codecs_decode_a_noiseless_codeword(name, K, N, kw):
    cdc = getattr(af.codec, name)(K, N, **kw)
    enc, dec = cdc.encoder, cdc.decoder_siho
    u = spu.array(np.random.default_rng(1).integers(0, 2, enc.K).tolist(), dtype=spu.int32)
    dec.decode_siho(llr_of(enc.encode(u)))
    np.testing.assert_array_equal(af.tools.hard(dec["decode_siho::V_K"]), u.numpy)


def test_codec_with_trellis_and_gf():
    assert len(af.codec.rsc(16, 38).trellis) > 0
    assert af.codec.bch(106, 127).GF.t == 3


def test_codec_errors():
    with pytest.raises(TypeError, match="unexpected keyword"):
        af.codec.polar(32, 64, dec_nope=1)
    with pytest.raises(TypeError, match="at most"):
        af.codec.polar(32, 64, None, None)


def test_modules_keep_the_codec_alive():
    import gc

    enc = af.codec.repetition(8, 24).encoder
    gc.collect()
    u = spu.array([1, 0, 1, 1, 0, 0, 1, 0], dtype=spu.int32)
    assert enc.encode(u).numpy.shape == (1, 24)
