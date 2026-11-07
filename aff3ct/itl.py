# -*- coding: utf-8 -*-
"""Interleavers: modules that apply the permutation of an interleaver core (``aff3ct.tools.Interleaver_core_*``).

>>> core = af.tools.Interleaver_core_random(64, seed=1)
>>> itl = af.itl.Interleaver(core)               # D = int32 by default
>>> itl_r = af.itl.Interleaver(core, D=spu.float32)

Class templates are grouped by dtype combination (``isinstance(x, itl.<Class>)`` whatever the dtypes,
``itl.<Class>[streampu.int32]`` for one instance); see :class:`aff3ct._dispatch.Template`.
"""

from aff3ct import _ext
from aff3ct._dispatch import export, export_functions

__all__ = export(_ext.itl, globals()) + export_functions(globals(), "itl")
