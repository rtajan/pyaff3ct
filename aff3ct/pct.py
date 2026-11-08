# -*- coding: utf-8 -*-
"""Puncturers.

Class templates are grouped by dtype combination (``isinstance(x, pct.<Class>)`` whatever the dtypes,
``pct.<Class>[streampu.int32]`` for one instance); see ``aff3ct._dispatch.Template``.
"""

from aff3ct import _ext
from aff3ct._dispatch import export, export_functions

__all__ = export(_ext.pct, globals()) + export_functions(globals(), "pct")
