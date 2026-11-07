# -*- coding: utf-8 -*-
"""Quantizers (fixed-point LLRs).

Class templates are grouped by dtype combination (``isinstance(x, qnt.<Class>)`` whatever the dtypes,
``qnt.<Class>[streampu.int32]`` for one instance); see :class:`aff3ct._dispatch.Template`.
"""

from aff3ct import _ext
from aff3ct._dispatch import export, export_functions

__all__ = export(_ext.qnt, globals()) + export_functions(globals(), "qnt")
