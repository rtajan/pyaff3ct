# -*- coding: utf-8 -*-
"""Extractors (systematic / parity LLRs, used by the turbo schemes).

Class templates are grouped by dtype combination (``isinstance(x, ext.<Class>)`` whatever the dtypes,
``ext.<Class>[streampu.int32]`` for one instance); see :class:`aff3ct._dispatch.Template`.
"""

from aff3ct import _ext
from aff3ct._dispatch import export

__all__ = export(_ext.ext, globals())
