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


__all__ = sorted(export(_ext.tools, globals()) + export_functions(globals(), "tools") + ["hard", "sigma_from_ebn0"])
