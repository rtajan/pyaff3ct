"""P0 tools: interleaver cores and interleavers, frozen bits generators, noise conversions, interface accessors."""

import gc
import io
import math

import numpy as np
import pytest
import streampu as spu

import aff3ct as af


# ----------------------------------------------------------------------------------------------- noise conversions
def test_noise_conversions_round_trip():
    esn0 = af.tools.ebn0_to_esn0(2.0, code_rate=0.5, bps=2)
    assert esn0 == pytest.approx(2.0 + 10 * math.log10(0.5 * 2))
    assert af.tools.esn0_to_ebn0(esn0, code_rate=0.5, bps=2) == pytest.approx(2.0)
    sigma = af.tools.esn0_to_sigma(esn0)
    assert sigma == pytest.approx(math.sqrt(1 / (2 * 10 ** (esn0 / 10))))
    # AFF3CT: sigma_to_esn0 = 10 log10(1 / sigma^2) is not the inverse of esn0_to_sigma (factor 2: 3.01 dB)
    assert af.tools.sigma_to_esn0(sigma) == pytest.approx(esn0 + 10 * math.log10(2))


def test_sigma_from_ebn0():
    s = af.tools.sigma_from_ebn0(3.0, code_rate=0.5)
    assert isinstance(s, af.tools.Sigma[spu.float32])
    assert s.ebn0 == pytest.approx(3.0) and s.esn0 == pytest.approx(3.0 + 10 * math.log10(0.5))
    assert s.sigma == pytest.approx(af.tools.esn0_to_sigma(s.esn0), rel=1e-6)
    assert isinstance(af.tools.sigma_from_ebn0(1.0, R=spu.float64), af.tools.Sigma[spu.float64])


def test_templates_are_callable_with_dtype_keywords():
    assert isinstance(af.tools.Sigma(0.5), af.tools.Sigma[spu.float32])
    assert isinstance(af.tools.Sigma(0.5, R=spu.float64), af.tools.Sigma[spu.float64])
    with pytest.raises(TypeError):
        af.tools.Sigma(0.5, R=spu.int8)


# ----------------------------------------------------------------------------------------------- interleavers
@pytest.mark.parametrize(
    "make",
    [
        lambda n: af.tools.Interleaver_core_NO(n),
        lambda n: af.tools.Interleaver_core_random(n, seed=3),
        lambda n: af.tools.Interleaver_core_golden(n, seed=3),
        lambda n: af.tools.Interleaver_core_random_column(n, n_cols=4),
        lambda n: af.tools.Interleaver_core_row_column(n, n_cols=4),
        lambda n: af.tools.Interleaver_core_column_row(n, n_cols=4, read_order="BOTTOM_RIGHT"),
        lambda n: af.tools.Interleaver_core_LTE(40),
        lambda n: af.tools.Interleaver_core_CCSDS(1784),
    ],
)
def test_interleaver_cores_are_permutations(make):
    core = make(64)
    assert isinstance(core, af.tools.Interleaver_core)
    lut, inv = core.lut, core.lut_inv
    assert len(core) == core.size == lut.size
    np.testing.assert_array_equal(np.sort(lut), np.arange(core.size))
    np.testing.assert_array_equal(lut[inv], np.arange(core.size))


def test_interleaver_core_dtypes():
    assert isinstance(af.tools.Interleaver_core_random(16), af.tools.Interleaver_core_random[spu.uint32])
    assert isinstance(af.tools.Interleaver_core_random(16, T=spu.uint16), af.tools.Interleaver_core[spu.uint16])


@pytest.mark.parametrize("D", [spu.int32, spu.float32, spu.int8])
def test_interleaver_module(D):
    core = af.tools.Interleaver_core_random(32, seed=7)
    itl = af.itl.Interleaver(core, D=D)
    assert isinstance(itl, af.itl.Interleaver) and isinstance(itl, spu.Module)
    assert itl.core.size == 32
    x = spu.array(list(range(32)), dtype=D)
    y = itl.interleave(x)
    np.testing.assert_array_equal(y.numpy[0], x.numpy[0][core.lut])
    z = itl.deinterleave(y)
    np.testing.assert_array_equal(z.numpy, x.numpy)


def test_interleaver_keeps_its_core_alive():
    itl = af.itl.Interleaver(af.tools.Interleaver_core_LTE(40))
    import gc

    gc.collect()
    x = spu.array(list(range(40)), dtype=spu.int32)
    np.testing.assert_array_equal(np.sort(itl.interleave(x).numpy[0]), np.arange(40))


def test_interleaver_functions():
    core = af.tools.interleaver_core(size=24, type="RANDOM", seed=2)
    assert isinstance(core, af.tools.Interleaver_core_random)  # most derived registered class
    itl = af.itl.interleaver(core, D=spu.float32)
    assert isinstance(itl, af.itl.Interleaver[spu.float32])


# ----------------------------------------------------------------------------------------------- frozen bits
def test_frozen_bits_generator_ga():
    K, N = 32, 64
    gen = af.tools.Frozenbits_generator_GA_Arikan(K, N)
    assert (gen.K, gen.N) == (K, N)
    fb = gen.generate(af.tools.sigma_from_ebn0(2.0, code_rate=K / N))
    assert fb.dtype == np.bool_ and fb.size == N and fb.sum() == N - K
    assert not fb[-1] and fb[0]  # last channel the most reliable, first one the least
    assert sorted(gen.best_channels.tolist()) == list(range(N))
    assert isinstance(gen.noise, af.tools.Noise)
    np.testing.assert_array_equal(gen.generate(), fb)  # same noise kept


def test_frozen_bits_generator_needs_a_noise():
    with pytest.raises(Exception):
        af.tools.Frozenbits_generator_GA_Arikan(8, 16).generate()


def test_frozen_bits_generator_bec():
    fb = af.tools.Frozenbits_generator_BEC(8, 16).generate(af.tools.Event_probability[spu.float32](0.3))
    assert fb.sum() == 8


def test_frozen_bits_function_and_polar_chain():
    K, N = 32, 64
    gen = af.tools.frozenbits_generator(K, N, type="GA", noise=0.6)  # float noise: sigma of the factory
    assert isinstance(gen, af.tools.Frozenbits_generator_GA_Arikan)
    fb = gen.generate(af.tools.Sigma(0.6))
    enc = af.enc.polar(K, N, fb)
    dec = af.dec.polar(K, N, fb, type="SC", implem="NAIVE")
    np.testing.assert_array_equal(enc.frozen_bits, fb)
    np.testing.assert_array_equal(dec.frozen_bits, fb)


# ----------------------------------------------------------------------------------------------- interface accessors
def test_interface_accessors_on_module_bases():
    K, N = 8, 16
    fb = np.zeros(N, dtype=bool)
    fb[: N - K] = True
    dec = af.dec.polar(K, N, fb, type="SC", implem="NAIVE")
    assert isinstance(dec, af.dec.Decoder_SIHO)
    assert hasattr(dec, "frozen_bits") and not hasattr(dec, "pretransform")
    fb2 = fb[::-1].copy()
    dec.set_frozen_bits(fb2)
    np.testing.assert_array_equal(dec.frozen_bits, fb2)

    rep = af.enc.repetition(K, 3 * K)
    assert not hasattr(rep, "frozen_bits") and not hasattr(rep, "trellis")
    with pytest.raises(AttributeError, match="Interface_get_set_frozen_bits"):
        rep.set_frozen_bits(fb)

    rsc = af.enc.rsc(K, 2 * K + 2 * 3)  # RSC, memory 3: tail bits
    assert len(rsc.trellis) > 0


# ----------------------------------------------------------------------------------------------- sparse matrices
HAMMING_H = np.array([[1, 1, 0, 1, 1, 0, 0], [1, 0, 1, 1, 0, 1, 0], [0, 1, 1, 1, 0, 0, 1]])


def test_sparse_matrix_conversions():
    H = af.tools.Sparse_matrix(HAMMING_H)
    assert H.shape == (3, 7) and H.n_connections == HAMMING_H.sum()
    np.testing.assert_array_equal(H.to_dense(), HAMMING_H)
    np.testing.assert_array_equal(np.asarray(H), HAMMING_H)
    assert H[0, 1] and not H[0, 2] and H.at(2, 6)
    assert H.row_to_cols[0] == [0, 1, 3, 4]
    np.testing.assert_array_equal(H.T.to_dense(), HAMMING_H.T)
    rows, cols = H.nonzero()
    np.testing.assert_array_equal(HAMMING_H[rows, cols], 1)
    assert H == af.tools.Sparse_matrix(HAMMING_H.astype(bool)) and H != H.T
    H2 = af.tools.Sparse_matrix(3, 7)
    for r, c in zip(rows, cols):
        H2.add_connection(r, c)
    assert H2 == H
    assert "3x7" in repr(H)


def test_sparse_matrix_scipy():
    sparse = pytest.importorskip("scipy.sparse")
    H = af.tools.Sparse_matrix(HAMMING_H)
    S = H.to_scipy()
    assert sparse.issparse(S) and S.shape == (3, 7)
    np.testing.assert_array_equal(S.toarray(), HAMMING_H)
    assert af.tools.Sparse_matrix.from_scipy(sparse.coo_matrix(HAMMING_H)) == H


def test_alist_round_trip(tmp_path):
    H = af.tools.Sparse_matrix(HAMMING_H)
    af.tools.AList.write(H, tmp_path / "h.alist")
    H2 = af.tools.AList.read(str(tmp_path / "h.alist"))
    assert H2 == H.turn(H2.way)  # AList stores the matrix vertically (N rows)
    assert sorted(af.tools.AList.read_matrix_size(tmp_path / "h.alist")) == [3, 7]
    H3, info_bits_pos, pct = af.tools.LDPC_matrix_handler.read(tmp_path / "h.alist")
    assert H3 == H2 and info_bits_pos.size == 0 and len(pct) == 0
    with pytest.raises(ValueError, match="cannot open"):
        af.tools.AList.read(tmp_path / "missing.alist")


def test_generator_matrix():
    H = af.tools.Sparse_matrix(HAMMING_H)
    G, info_bits_pos = af.tools.LDPC_matrix_handler.transform_H_to_G(H)
    assert len(info_bits_pos) == 4 and af.tools.LDPC_matrix_handler.check_info_pos(info_bits_pos, 4, 7)
    assert af.tools.LDPC_matrix_handler.check_GH(H, G)
    with pytest.raises(ValueError):
        af.tools.LDPC_matrix_handler.transform_H_to_G(H, "NOPE")


def test_ldpc_chain_from_a_matrix():
    # AFF3CT stores H vertically (N rows x M columns, as the AList files)
    H = af.tools.Sparse_matrix(HAMMING_H).turn(af.tools.Matrix.Way.VERTICAL)
    assert H.shape == (7, 3)
    enc = af.enc.ldpc(4, 7, af.tools.Sparse_matrix(), H, type="LDPC_H")
    dec = af.dec.ldpc(4, 7, H, enc.info_bits_pos, type="BP_FLOODING", implem="SPA", n_ite=10)
    u = spu.array([1, 0, 1, 1], dtype=spu.int32)
    x = enc.encode(u)
    assert enc.is_codeword(x.numpy[0])
    dec.decode_siho(spu.array((1.0 - 2.0 * x.numpy[0]).tolist(), dtype=spu.float32))
    np.testing.assert_array_equal(dec["decode_siho::V_K"].numpy, u.numpy)


# ----------------------------------------------------------------------------------------------- Galois / BCH / RS
def test_bch_polynomial_generator_and_chain():
    GF = af.tools.BCH_polynomial_generator(15, 2)
    assert isinstance(GF, af.tools.Galois) and isinstance(GF, af.tools.BCH_polynomial_generator[spu.int32])
    assert (GF.N, GF.m, GF.t, GF.n_rdncy) == (15, 4, 2, 8)
    K = GF.N - GF.n_rdncy
    enc, dec = af.enc.bch(K, GF.N, GF), af.dec.bch(K, GF.N, GF)
    u = spu.array([1, 0, 1, 1, 0, 0, 1], dtype=spu.int32)
    x = enc.encode(u).numpy[0].copy()
    x[[2, 9]] ^= 1  # two errors: corrected
    dec.decode_hiho(spu.array(x.tolist(), dtype=spu.int32))
    np.testing.assert_array_equal(dec["decode_hiho::V_K"].numpy, u.numpy)


def test_rs_polynomial_generator():
    GF = af.tools.RS_polynomial_generator(15, 2)
    assert isinstance(GF, af.tools.Galois[spu.int32]) and (GF.m, GF.n_rdncy) == (4, 4)
    enc = af.enc.rs(GF.N - GF.n_rdncy, GF.N, GF)  # sizes in symbols; the module works on bits
    assert (enc.K, enc.N) == (11 * 4, 15 * 4)
    dec = af.dec.rs(GF.N - GF.n_rdncy, GF.N, GF)
    u = spu.array(np.random.default_rng(1).integers(0, 2, 44).tolist(), dtype=spu.int32)
    x = enc.encode(u).numpy[0].copy()
    x[[0, 1, 2, 3, 20]] ^= 1  # two symbol errors: corrected
    dec.decode_hiho(spu.array(x.tolist(), dtype=spu.int32))
    np.testing.assert_array_equal(dec["decode_hiho::V_K"].numpy, u.numpy)


# ----------------------------------------------------------------------------------------------- monitor and reporters
def test_monitor_bfer_and_reporters():
    mnt = af.mnt.bfer(4, n_frame_errors=2)
    assert isinstance(mnt, af.mnt.Monitor_BFER[spu.int32]) and mnt.max_fe == 2
    fe = []
    mnt.record_callback_fe(lambda n_be, frame: fe.append(n_be))
    mnt.check_errors(spu.array([1, 0, 1, 1], dtype=spu.int32), spu.array([1, 1, 1, 0], dtype=spu.int32))
    mnt.check_errors(spu.array([1, 0, 1, 1], dtype=spu.int32), spu.array([1, 0, 1, 1], dtype=spu.int32))
    assert (mnt.n_analyzed_frames, mnt.n_fe, mnt.n_be, fe) == (2, 1, 2, [2])
    assert mnt.fer == pytest.approx(0.5) and mnt.ber == pytest.approx(0.25) and not mnt.is_done()

    total = af.mnt.Monitor_BFER(4, 10)
    total.collect(mnt)
    total += mnt
    assert total.n_fe == 2

    reporters = [
        af.tools.Reporter_noise(af.tools.sigma_from_ebn0(1.0), show_sigma=True),
        af.tools.Reporter_BFER(mnt),
        af.tools.Reporter_throughput(mnt),
    ]
    assert all(isinstance(r, spu.Reporter) for r in reporters)
    ter = spu.Terminal_std(reporters)
    out = io.StringIO()
    ter.legend(out)
    ter.final_report(out)
    out = out.getvalue()
    assert "FER" in out and "Eb/N0" in out and "SIM_THR" in out


def test_terminal_keeps_its_reporters_alive():
    # streampu >= 1.2.1: Terminal_std keeps the reporters given in a temporary list
    mnt = af.mnt.Monitor_BFER(4, 1)
    ter = spu.Terminal_std([af.tools.Reporter_BFER(mnt), af.tools.Reporter_noise(af.tools.sigma_from_ebn0(1.0))])
    gc.collect()
    out = io.StringIO()
    ter.legend(out)  # reads the reporters (a dangling one would crash or print garbage)
    ter.final_report(out)
    assert "FER" in out.getvalue() and "Eb/N0" in out.getvalue()


def test_reporters_keep_their_objects_alive():
    import gc

    rep = af.tools.Reporter_BFER(af.mnt.Monitor_BFER(4, 1))
    rep_n = af.tools.Reporter_noise(af.tools.sigma_from_ebn0(1.0))
    gc.collect()
    ter = spu.Terminal_std([rep, rep_n])
    ter.final_report()


# ----------------------------------------------------------------------------------------------- shared BFER monitor
def _chain_with(mnt, K=32, N=64):
    fb = af.tools.Frozenbits_generator_GA_Arikan(K, N).generate(af.tools.Sigma(1.0))
    src, enc = af.src.source(K, type="RAND", seed=0), af.enc.polar(K, N, fb)
    mdm, chn = af.mdm.modem(N, type="BPSK"), af.chn.channel(N, type="AWGN", seed=1)
    dec = af.dec.polar(K, N, fb, type="SC", implem="NAIVE")
    sigma = spu.array([1.0], dtype=spu.float32)  # high noise: about one frame error out of two
    u = src.generate()[0]
    dec.decode_siho(mdm.demodulate(sigma, chn.add_noise(sigma, mdm.modulate(enc.encode(u)))))
    mnt.check_errors(u, dec["decode_siho::V_K"])
    return mnt


@pytest.mark.parametrize("n_threads", [1, 4])
def test_monitor_bfer_ar_stops_on_the_total(n_threads):
    max_fe = 50
    mnt = _chain_with(af.mnt.Monitor_BFER_AR(32, max_fe))
    assert isinstance(mnt, af.mnt.Monitor_BFER_AR[spu.int32]) and isinstance(mnt, af.mnt.Monitor_BFER)
    seq = spu.Sequence(mnt["check_errors::status"], n_threads=n_threads)
    clones = seq.get_cloned_modules(mnt)
    assert all(c.is_shared_with(mnt) for c in clones)
    assert not af.mnt.Monitor_BFER_AR(32, max_fe).is_shared_with(mnt)
    for _ in range(2):  # two SNR points: reset() of the original resets the totals of every thread
        mnt.reset()
        assert mnt.n_fe == 0 and not mnt.is_done()
        seq.exec()
        # the original shows the totals: every thread stopped at max_fe frame errors (+ the frames in flight)
        assert max_fe <= mnt.n_fe < max_fe + n_threads
        # a clone keeps the totals of its last frame; is_done() refreshes them
        assert mnt.is_done() and all(c.is_done() for c in clones)
        assert all((c.n_fe, c.n_analyzed_frames) == (mnt.n_fe, mnt.n_analyzed_frames) for c in clones)
        assert mnt.fer == pytest.approx(mnt.n_fe / mnt.n_analyzed_frames)
    out = io.StringIO()
    rep = af.tools.Reporter_BFER(mnt)
    spu.Terminal_std([rep]).final_report(out)
    assert str(mnt.n_fe) in out.getvalue()


def test_monitor_bfer_with_threads_stops_on_one_clone():
    # the reason of Monitor_BFER_AR: with Monitor_BFER, each thread counts alone (the original monitor is the one of
    # the first thread at most) and the sequence stops when one of them reaches max_fe. How much the other threads did
    # depends on the scheduling (on a loaded machine one thread may do all the work): not checked.
    mnt = _chain_with(af.mnt.Monitor_BFER(32, 50))
    seq = spu.Sequence(mnt["check_errors::status"], n_threads=4)
    seq.exec()
    clones = seq.get_cloned_modules(mnt)
    assert max(c.n_fe for c in clones) == 50


def test_monitor_bfer_ar_callbacks_prevent_cloning():
    mnt = _chain_with(af.mnt.Monitor_BFER_AR(32, 10))
    mnt.record_callback_check(lambda: None)
    with pytest.raises(spu.exceptions.RuntimeError, match="clone"):
        spu.Sequence(mnt["check_errors::status"], n_threads=2)


# ----------------------------------------------------------------------------------------------- polar tools
def test_polar_code_and_other_frozen_bits_generators():
    code = af.tools.Polar_code(16, [[1, 0], [1, 1]])
    assert code.N == 16 and code.is_mono_kernel() and code.can_be_systematic()
    mk = af.tools.Polar_code([[[1, 0], [1, 1]], [[1, 1, 1], [1, 0, 1], [0, 1, 1]]], [0, 1])
    assert mk.N == 6 and not mk.is_mono_kernel()
    ga = af.tools.Frozenbits_generator_GA(8, 16, code)
    np.testing.assert_array_equal(ga.generate(af.tools.Sigma(0.8)),
                                  af.tools.Frozenbits_generator_GA_Arikan(8, 16).generate(af.tools.Sigma(0.8)))
    assert af.tools.Frozenbits_generator_GA(3, 6, mk).generate(af.tools.Sigma(0.8)).sum() == 3
    rm = af.tools.Frozenbits_generator_RM(8, 16).generate()
    assert rm.sum() == 8
    # reads the 5G sequence of the AFF3CT configuration files at generate()
    assert isinstance(af.tools.Frozenbits_generator_5G(32, 64), af.tools.Frozenbits_generator_file)


def test_from_cli_not_strict():
    cmd = "-C POLAR -K 32 -N 64 --crc-poly 8-DVB-S2 --dec-type SCL -L 4 --chn-type AWGN"
    with pytest.raises(ValueError, match="Unknown argument"):
        af.factory.CRC.from_cli(cmd)
    crc = af.factory.CRC.from_cli(cmd, strict=False)
    assert crc.type == "8-DVB-S2"
    dec = af.factory.Decoder_polar.from_cli(cmd, strict=False)
    assert (dec.type, dec.L) == ("SCL", 4)
