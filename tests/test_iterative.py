"""Iterative receivers: decoders that keep their state across the iterations of a frame (tools.reset_decoders_on_check)."""

from pathlib import Path

import pytest
import streampu as spu

import aff3ct as af

H = Path(__file__).resolve().parent.parent / "lib" / "aff3ct" / "conf" / "dec" / "LDPC" / "CCSDS_64_128.alist"
pytestmark = pytest.mark.skipif(not H.exists(), reason="LDPC matrices of AFF3CT not fetched")


def chain(n_threads, monitor=True):
    K = 64
    cdc = af.codec.ldpc(K, 128, enc_type="LDPC_H", dec_H_path=str(H), dec_type="BP_HORIZONTAL_LAYERED", dec_n_ite=5)
    src = af.src.source(K, type="RAND")
    mdm = af.mdm.modem(cdc.encoder.N, type="BPSK")
    chn = af.chn.channel(cdc.encoder.N, type="AWGN")
    sigma = spu.array([0.8], dtype=spu.float32)
    u = src.generate()[0]
    llr = mdm.demodulate(sigma, chn.add_noise(sigma, mdm.modulate(cdc.encoder.encode(u))))
    ext = cdc.decoder_siso.decode_siso(llr)[1]
    if not monitor:
        return spu.Sequence(ext, n_threads=n_threads), cdc, None
    mnt = af.mnt.Monitor_BFER_AR(K, 10**6, max_n_frames=20)
    mnt.check_errors(u, cdc.decoder_siho.decode_siho(ext)[1])
    return spu.Sequence(mnt["check_errors::status"], n_threads=n_threads), cdc, mnt


def test_decoders_reset_after_each_checked_frame():
    seq, cdc, mnt = chain(2)
    assert af.tools.reset_decoders_on_check(seq) == 2
    decoders = [m for ms in seq.get_modules_per_threads() for m in ms if isinstance(m, af.dec.Decoder_SISO)]
    assert len(decoders) == 2 and not any(d.is_auto_reset() for d in decoders)
    seq.exec()
    assert mnt.n_analyzed_frames >= 20


def test_one_monitor_per_thread_required():
    seq, _, _ = chain(1, monitor=False)
    with pytest.raises(ValueError, match="one BFER monitor per thread"):
        af.tools.reset_decoders_on_check(seq)
