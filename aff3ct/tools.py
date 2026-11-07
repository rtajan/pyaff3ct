# -*- coding: utf-8 -*-
"""AFF3CT tools (noise...).

Class templates are grouped by dtype combination (``isinstance(x, tools.<Class>)`` whatever the dtypes,
``tools.<Class>[streampu.int32]`` for one instance); see :class:`aff3ct._dispatch.Template`.
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


__all__ = sorted(export(_ext.tools, globals()) + export_functions(globals(), "tools") + ["hard"])
