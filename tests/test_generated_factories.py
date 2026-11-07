"""Generated factories and module-level functions (scripts/gen_factories.py, Plan.md phase 2)."""

import gc
import inspect

import numpy as np
import pytest
import streampu as spu

import aff3ct as af
from aff3ct._generated import functions as F

NOT_CONSTRUCTIBLE = {"Decoder", "Codec"}  # family bases (no public / an ambiguous constructor)
K, N = 8, 16


def _factories():
    return {n: c for n, c in vars(af.factory).items() if isinstance(c, type) and issubclass(c, af.factory.Factory)}


def frozen_bits(K=K, N=N):
    # any mask works for a noiseless check; the first N - K bits are frozen
    fb = np.zeros(N, dtype=bool)
    fb[: N - K] = True
    return fb


def decoded(sock):
    # AFF3CT convention: a bit is 0 or non-zero (the FAST decoders return the sign bit set for a 1)
    return (sock.numpy != 0).astype(np.int64)


def bits(n, seed=0, dtype=spu.int32):
    return spu.array(np.random.default_rng(seed).integers(0, 2, n).tolist(), dtype=dtype)


def test_every_factory_is_bound():
    facs = _factories()
    assert len(facs) >= 80  # Factory + 79 generated
    for name, cls in facs.items():
        if cls is af.factory.Factory or name in NOT_CONSTRUCTIBLE:
            continue
        f = cls()
        assert set(f.parameters) == set(cls._parameters), name
        assert repr(f).startswith(f"{name}(")


def test_parameters_are_inherited_in_declaration_order():
    f = af.factory.Decoder_polar(K=K, N_cw=N, type="SCL", L=4)
    keys = list(f.parameters)
    assert keys[:4] == ["K", "N_cw", "type", "implem"]  # declared by factory::Decoder first
    assert (f.K, f.N_cw, f.type, f.L) == (K, N, "SCL", 4)


def test_from_cli_on_generated_factories():
    f = af.factory.Decoder_polar.from_cli("--dec-type SCL --dec-implem NAIVE --dec-lists 4", K=K, N_cw=N)
    assert (f.type, f.implem, f.L) == ("SCL", "NAIVE", 4)


def test_sub_factories_are_references():
    itl = af.factory.Interleaver()
    core = itl.core
    assert isinstance(core, af.factory.Interleaver_core)
    core.type = "LTE"
    assert itl.core.type == "LTE"  # same object, owned by the parent factory


def test_function_signatures_follow_the_rules():
    sig = inspect.signature(af.dec.polar)
    kinds = {n: p.kind for n, p in sig.parameters.items()}
    P, KW = inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY
    # sizes then builder arguments are positional; the factory parameters and the dtypes are keyword-only
    assert [n for n, k in kinds.items() if k == P] == ["K", "N_cw", "frozen_bits", "crc", "encoder"]
    assert {"type", "implem", "L", "n_ite", "B", "Q"} <= {n for n, k in kinds.items() if k == KW}
    assert af.dec.polar.__module__ == "aff3ct.dec" and af.dec.polar.__name__ == "polar"
    assert "Compiled dtype combinations" in af.dec.polar.__doc__
    # one function per builder
    assert callable(af.dec.polar_siso) and callable(af.dec.polar_gen)
    assert inspect.signature(af.mdm.modem).parameters["N"].kind == P


def test_functions_are_generated_only_for_wrapped_classes():
    assert not hasattr(af.tools, "frozenbits_generator")  # tools::Frozenbits_generator not wrapped yet
    assert any(s.startswith("Frozenbits_generator.build") for s in F.SKIPPED)


def test_polar_encoder_and_decoder_noiseless():
    fb = frozen_bits()
    enc = af.enc.polar(K, N, fb)
    dec = af.dec.polar(K, N, fb, type="SC", implem="NAIVE")
    assert isinstance(enc, af.enc.Encoder[spu.int32]) and (enc.K, enc.N) == (K, N)
    assert isinstance(dec, af.dec.Decoder_SIHO[spu.int32, spu.float32])
    u = bits(K)
    x = enc.encode(u)  # one output: X_N
    llr = spu.array((1.0 - 2.0 * x.numpy[0]).astype(np.float32).tolist(), dtype=spu.float32)
    dec.decode_siho(llr)  # several outputs (CWD, V_K): read them by name
    np.testing.assert_array_equal(dec["decode_siho::V_K"].numpy, u.numpy)


@pytest.mark.parametrize("B, Q", [(spu.int8, spu.int8), (spu.int16, spu.int16), (spu.int32, spu.float32)])
def test_polar_fast_decoder_by_dtype(B, Q):
    K, N = 32, 64  # the FAST SC decoder unrolls the first 6 levels: N >= 64
    fb = frozen_bits(K, N)
    enc = af.enc.polar(K, N, fb, B=B)
    dec = af.dec.polar(K, N, fb, type="SC", implem="FAST", B=B)  # Q: only compatible value with B
    assert isinstance(dec, af.dec.Decoder_SIHO[B, Q])
    u = bits(K, dtype=B)
    x = enc.encode(u)
    llr = spu.array((1 - 2 * x.numpy[0].astype(np.int64)).tolist(), dtype=Q)
    dec.decode_siho(llr)
    np.testing.assert_array_equal(decoded(dec["decode_siho::V_K"]), u.numpy)


def test_siso_builder():
    dec = af.dec.polar_siso(K, N, frozen_bits(), type="SCAN", implem="NAIVE")
    assert isinstance(dec, af.dec.Decoder_SISO[spu.int32, spu.float32])


def test_builder_arguments_are_kept_alive():
    K, N = 16, 32
    crc = af.crc.crc(K - 8, type="8-DVB-S2")  # the CA-SCL decoder checks K - 8 information bits + 8 CRC bits
    assert crc.size == 8
    fb = frozen_bits(K, N)
    enc = af.enc.polar(K, N, fb)
    dec = af.dec.polar(K, N, fb, crc=crc, type="SCL", L=4, implem="NAIVE")
    u = bits(K - 8)
    x = enc.encode(crc.build(u))
    del crc
    gc.collect()  # the CRC is used by the decoder: it must still be alive
    llr = spu.array((1.0 - 2.0 * x.numpy[0]).astype(np.float32).tolist(), dtype=spu.float32)
    dec.decode_siho(llr)
    np.testing.assert_array_equal(dec["decode_siho::V_K"].numpy[..., : K - 8], u.numpy)


def test_explicit_factory_with_builder_keywords():
    f = af.factory.Decoder_polar(K=K, N_cw=N, type="SC", implem="NAIVE")
    dec = f.build(frozen_bits(), B=spu.int16)  # positional builder argument + dtype keyword
    assert isinstance(dec, af.dec.Decoder_SIHO[spu.int16, spu.int16])
    with pytest.raises(TypeError, match="not compiled for"):
        f.build(frozen_bits(), B=spu.int16, Q=spu.float32)


def test_positional_sizes_of_the_families():
    assert list(inspect.signature(af.mnt.bfer).parameters)[:1] == ["K"]  # declared by Monitor_BFER (Monitor: none)
    assert list(inspect.signature(af.dec.ldpc).parameters)[:2] == ["K", "N_cw"]  # N of Decoder_LDPC stays a keyword
    assert inspect.signature(af.dec.ldpc).parameters["N"].kind == inspect.Parameter.KEYWORD_ONLY


def test_bpsk_awgn_polar_chain():
    fb = frozen_bits()
    src = af.src.source(K, type="RAND", seed=3)
    enc = af.enc.polar(K, N, fb)
    mdm = af.mdm.modem(N, type="BPSK")
    chn = af.chn.channel(N, type="AWGN", seed=5)
    dec = af.dec.polar(K, N, fb, type="SC", implem="NAIVE")
    mnt = af.mnt.bfer(K, n_frame_errors=10)
    assert isinstance(mdm, af.mdm.Modem) and isinstance(chn, af.chn.Channel) and isinstance(mnt, af.mnt.Monitor)

    sigma = spu.array([0.05], dtype=spu.float32)  # almost noiseless: no error expected
    u = src.generate()[0]
    y = chn.add_noise(sigma, mdm.modulate(enc.encode(u)))
    dec.decode_siho(mdm.demodulate(sigma, y))
    v = dec["decode_siho::V_K"]
    mnt.check_errors(u, v)
    np.testing.assert_array_equal(v.numpy, u.numpy)


def test_later_builder_argument_without_the_previous_ones():
    # build(frozen_bits, crc = nullptr, encoder = nullptr): encoder= alone (regression: no overload matched)
    K, N = 8, 16
    fb = frozen_bits(K, N)
    enc = af.enc.polar(K, N, fb)
    dec = af.dec.polar(K, N, fb, encoder=enc, type="ML", implem="STD")
    u = bits(K)
    x = enc.encode(u)
    dec.decode_siho(spu.array((1.0 - 2.0 * x.numpy[0]).astype(np.float32).tolist(), dtype=spu.float32))
    np.testing.assert_array_equal(decoded(dec["decode_siho::V_K"]), u.numpy)
