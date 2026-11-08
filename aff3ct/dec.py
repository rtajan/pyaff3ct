# -*- coding: utf-8 -*-
"""Decoders (hard-input hard-output, soft-input hard-output, soft-input soft-output).

Class templates are grouped by dtype combination (``isinstance(x, dec.<Class>)`` whatever the dtypes,
``dec.<Class>[streampu.int32]`` for one instance); see ``aff3ct._dispatch.Template``.
"""

from aff3ct import _ext
from aff3ct._dispatch import export, export_functions

__all__ = export(_ext.dec, globals()) + export_functions(globals(), "dec")
