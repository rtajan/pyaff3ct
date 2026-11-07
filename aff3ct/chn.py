# -*- coding: utf-8 -*-
"""Channels (AWGN, Rayleigh, BEC, BSC, optical...).

Class templates are grouped by dtype combination (``isinstance(x, chn.<Class>)`` whatever the dtypes,
``chn.<Class>[streampu.int32]`` for one instance); see :class:`aff3ct._dispatch.Template`.
"""

from aff3ct import _ext
from aff3ct._dispatch import export, export_functions

__all__ = export(_ext.chn, globals()) + export_functions(globals(), "chn")
