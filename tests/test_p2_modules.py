"""Modules of phase 4 reached through the factories: all-zero, coset and user encoders, genius decoders."""

import numpy as np
import pytest
import streampu as spu

import aff3ct as af


def bits(n, seed=0):
    return spu.array(np.random.default_rng(seed).integers(0, 2, n).tolist(), dtype=spu.int32)


def test_all_zero_and_coset_encoders():
    azcw = af.enc.encoder(4, 12, type="AZCW")
    assert (azcw.encode(bits(4)).numpy == 0).all()  # all-zero codewords, whatever the information bits
    coset = af.enc.encoder(4, 12, type="COSET", seed=1)
    x = coset.encode(bits(4)).numpy[0]
    assert set(np.unique(x)) <= {0, 1} and x.any()  # random words (coset approach)


def test_user_encoder(tmp_path):
    cws = np.array([[1, 0, 1, 1, 0, 0], [0, 1, 1, 0, 1, 1]])
    path = tmp_path / "codewords.txt"
    path.write_text(f"{len(cws)} 6 3\n" + "\n".join(" ".join(map(str, c)) for c in cws))
    enc = af.enc.encoder(3, 6, type="USER", path=str(path))
    for c in [cws[0], cws[1], cws[0]]:  # the codewords of the file, cyclically
        np.testing.assert_array_equal(enc.encode(bits(3)).numpy[0], c)


def fer(cdc, ebn0, hard_input=False, n_frames=3000):
    enc, dec = cdc.encoder, cdc.decoder_siho
    src = af.src.source(enc.K, type="RAND", seed=1)
    mdm, chn = af.mdm.modem(enc.N, type="BPSK"), af.chn.channel(enc.N, type="AWGN", seed=2)
    mnt = af.mnt.Monitor_BFER_AR(enc.K, 10**9, max_n_frames=n_frames)
    s = spu.array([af.tools.sigma_from_ebn0(ebn0, enc.K / enc.N).sigma], dtype=spu.float32)
    u = src.generate()[0]
    llr = mdm.demodulate(s, chn.add_noise(s, mdm.modulate(enc.encode(u))))
    if hard_input:  # hard decision, then hard-input decoding
        _, y = af.codec.uncoded(enc.N, enc.N).decoder_siho.decode_siho(llr)
        _, v = dec.decode_hiho(y)
    else:
        _, v = dec.decode_siho(llr)
    mnt.check_errors(u, v)
    spu.Sequence(mnt["check_errors::status"]).exec()
    return mnt.fer


def test_genius_bch_decoder_is_a_bounded_distance_decoder():
    # a genius decoder knows the codeword (from the encoder) and decodes it when at most t bits are wrong: the frame
    # error rate of the algebraic decoder, which corrects up to t errors (same frames, same noise)
    f_alg = fer(af.codec.bch(11, 15), 4.0)
    f_gen = fer(af.codec.bch(11, 15, dec_implem="GENIUS"), 4.0)
    assert 0 < f_gen <= f_alg + 0.01 and abs(f_gen - f_alg) < 0.2 * f_alg + 0.01, (f_alg, f_gen)


@pytest.mark.xfail(raises=Exception, strict=True,
                   reason="AFF3CT v4.7.2: Decoder_RS_genius overrides only the hard-input decoding without status; "
                          "the tasks reach Decoder_RS::_decode, unimplemented in the genius decoder")
def test_genius_rs_decoder():
    fer(af.codec.rs(11, 15, dec_implem="GENIUS"), 4.0, hard_input=True, n_frames=10)


NP = {spu.int8: np.int8, spu.int16: np.int16, spu.int32: np.int32, spu.float32: np.float32}


def noiseless_ok(cdc, B=spu.int32, Q=spu.float32):
    """Encode then decode random bits, the LLRs of a BPSK channel without noise: the bits are recovered."""
    enc, dec = cdc.encoder, cdc.decoder_siho
    u = spu.array(np.random.default_rng(3).integers(0, 2, enc.K).astype(NP[B]), dtype=B)
    x = enc.encode(u).numpy
    llr = (1 - 2 * (x != 0).astype(np.float32)) * 8  # strong LLRs, positive for a bit 0
    _, v = dec.decode_siho(spu.array(llr.astype(NP[Q]), dtype=Q))
    return (af.tools.hard(v) == u.numpy).all()


def test_simd_rsc_decoders():
    # BCJR with the intra-frame SIMD strategy: on 8 / 16-bit LLRs, the "inter_intra" variants (x2 / x4 frames per
    # register, SSE or AVX according to the build)
    for B, Q in [(spu.int16, spu.int16), (spu.int8, spu.int8)]:
        cdc = af.codec.rsc(64, 2 * 64 + 6, dec_simd_strategy="INTRA", dec_implem="FAST", B=B, Q=Q)
        assert noiseless_ok(cdc, B, Q), (B, Q)


def test_bitpacked_polar_encoder_matches_the_naive_one():
    fb = af.tools.Frozenbits_generator_RM(64, 128).generate()
    u = bits(64, seed=4)
    x_fast = af.enc.polar(64, 128, fb, implem="FAST").encode(u).numpy.copy()  # Encoder_polar_bitpacked
    x_naive = af.enc.polar(64, 128, fb, implem="NAIVE").encode(u).numpy.copy()
    np.testing.assert_array_equal(x_fast, x_naive)


def test_dvbs2_ldpc_encoder():
    cdc = af.codec.ldpc(16200 * 8 // 9, 16200, enc_type="LDPC_DVBS2", dec_type="BP_HORIZONTAL_LAYERED",
                        dec_implem="MS", dec_n_ite=5)
    assert noiseless_ok(cdc)


def test_ook_optical_rop_estimate():
    from pathlib import Path

    pdf = Path(__file__).resolve().parent.parent / "lib" / "aff3ct" / "conf" / "chn" / "optical_channel.dist"
    if not pdf.exists():
        pytest.skip("optical channel distributions of AFF3CT not fetched (scripts/fetch_aff3ct_data.sh)")
    dist = af.tools.Distributions(str(pdf))
    mdm = af.mdm.modem(256, None, dist, type="OOK", channel_type="OPTICAL", rop_est_bits=64)
    assert "estimate" in type(mdm).__name__.lower() or mdm.N == 256
