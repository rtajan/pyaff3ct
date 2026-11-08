# -*- coding: utf-8 -*-
"""AFF3CT tools (noise...).

Class templates are grouped by dtype combination (``isinstance(x, tools.<Class>)`` whatever the dtypes,
``tools.<Class>[streampu.int32]`` for one instance); see ``aff3ct._dispatch.Template``.
"""

from typing import Any

import numpy as np

from aff3ct import _ext
from aff3ct._dispatch import export, export_functions


def hard(x: Any) -> np.ndarray:
    """Bits as 0 / 1, whatever the AFF3CT representation.

    In AFF3CT a bit is 0 or *non-zero*: some decoders return another value than 1 for a 1 (the FAST polar decoders
    return the sign bit, ``-2147483648`` in ``int32``; see ``docs/design/bit_convention.md``), and the monitors compare
    the bits as booleans. ``hard`` gives the 0 / 1 view, for display or a NumPy comparison; the modules do not need it.

    Args:
        x (streampu.Socket | numpy.ndarray | array-like): bits in the AFF3CT representation (e.g.
            ``dec["decode_siho::V_K"]``).

    Returns:
        out (numpy.ndarray): same shape and dtype, values 0 / 1 (a new array: the socket data are not modified).

    Examples:
        >>> dec.decode_siho(llr)
        >>> af.tools.hard(dec["decode_siho::V_K"])
        array([[1, 0, 1, ...]], dtype=int32)
    """
    a = np.asarray(x.numpy if hasattr(x, "numpy") else x)
    return (a != 0).astype(a.dtype if a.dtype != np.bool_ else np.int8)


def sigma_from_ebn0(ebn0: float, code_rate: float = 1.0, bps: int = 1, upsample_factor: int = 1, R: Any = None) -> Any:
    """Gaussian noise of a given Eb/N0, with its Es/N0 (the conversion of the AFF3CT simulations).

    Args:
        ebn0 (float): Eb/N0 (dB).
        code_rate (float): code rate K / N.
        bps (int): number of bits per symbol of the modulation.
        upsample_factor (int): samples per symbol of the modulation.
        R (streampu.dtype, optional): dtype of the noise (default ``streampu.float32``, that of the modules).

    Returns:
        out (aff3ct.tools.Sigma): sigma, Eb/N0 and Es/N0 set.

    Examples:
        >>> s = af.tools.sigma_from_ebn0(2.0, code_rate=0.5)
        >>> s.sigma, s.ebn0, s.esn0
    """
    esn0 = _ext.tools.ebn0_to_esn0(ebn0, code_rate, bps)
    sigma = _ext.tools.esn0_to_sigma(esn0, upsample_factor)
    return Sigma(sigma, ebn0, esn0, R=R)  # noqa: F821  (exported above)


def seed_sequence(sequence: Any, seed: int = 0) -> list[int]:
    """Different seeds in the modules of every thread of a sequence, as the AFF3CT simulator.

    A ``streampu.Sequence`` copies the modules into each of its threads, random generators included: without new
    seeds, all the threads draw the same frames and the same noise, and a simulation on ``n`` threads gives no more
    information than one thread (``max_fe`` then counts the same frame errors ``n`` times). Call this function once,
    after the creation of the sequence: each module that has a seed (``streampu.Interface_set_seed``: sources,
    channels, encoders and decoders that draw random values) receives its own seed, drawn from a generator
    initialized with ``seed``. The interleavers keep theirs: an encoder and its decoder must keep the same
    permutation.

    Args:
        sequence (streampu.Sequence): the sequence, after its creation (its modules in every thread).
        seed (int): seed of the generator of the seeds; the same value gives the same simulation.

    Returns:
        out (list[int]): the seeds given, in the order of the modules (thread after thread).

    Examples:
        >>> seq = spu.Sequence(mnt["check_errors::status"], n_threads=4)
        >>> af.tools.seed_sequence(seq)
        >>> seq.exec()
    """
    from streampu import Interface_set_seed

    prng = np.random.Generator(np.random.MT19937(seed))
    seeds = []
    for modules in sequence.get_modules_per_threads():
        for module in modules:
            if isinstance(module, Interface_set_seed):
                seeds.append(int(prng.integers(0, 2**31 - 1)))
                module.set_seed(seeds[-1])
    return seeds


def reset_decoders_on_check(sequence: Any) -> int:
    """SISO decoders that keep their state across the iterations of a frame, reset after each checked frame.

    In an iterative receiver (turbo demodulation, see ``docs/guides/iterative.md``), the SISO decoder is called once
    per global iteration on the same frame. Some decoders carry information from one call to the next (the LDPC BP
    decoders keep their messages and the previous extrinsic information): by default every call starts from a blank
    state (``auto_reset``), and the iterations bring much less. As the AFF3CT simulator (``Simulation_BFER_ite``),
    this function disables the automatic reset of the ``aff3ct.dec.Decoder_SISO`` modules and resets them when the
    BFER monitor of their thread has checked a frame. Call it once, after the creation of the sequence.

    The monitors then hold these callbacks, and AFF3CT does not clone a monitor with callbacks: to build another
    sequence with the same modules, call ``mnt.clear_callbacks()`` first (or keep one sequence and change its inputs,
    the noise for instance, between the executions).

    Args:
        sequence (streampu.Sequence): the sequence, after its creation; each thread must contain one
            ``aff3ct.mnt.Monitor_BFER``.

    Returns:
        out (int): number of decoders configured (all the threads).

    Examples:
        >>> seq = spu.Sequence(mnt["check_errors::status"], n_threads=4)
        >>> af.tools.seed_sequence(seq)
        >>> af.tools.reset_decoders_on_check(seq)
        4
    """
    from aff3ct import dec, mnt
    n = 0
    for modules in sequence.get_modules_per_threads():
        monitors = [m for m in modules if isinstance(m, mnt.Monitor_BFER)]
        decoders = [m for m in modules if isinstance(m, dec.Decoder_SISO)]
        if decoders and len(monitors) != 1:
            raise ValueError(f"one BFER monitor per thread expected, found {len(monitors)}")
        for d in decoders:
            d.set_auto_reset(False)
            monitors[0].record_callback_check(d.reset)
            n += 1
    return n


__all__ = sorted(export(_ext.tools, globals()) + export_functions(globals(), "tools")
                 + ["hard", "reset_decoders_on_check", "seed_sequence", "sigma_from_ebn0"])
