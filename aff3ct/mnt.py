# -*- coding: utf-8 -*-
"""Monitors (bit/frame error rate, EXIT chart, mutual information).

Class templates are grouped by dtype combination (``isinstance(x, mnt.<Class>)`` whatever the dtypes,
``mnt.<Class>[streampu.int32]`` for one instance); see :class:`aff3ct._dispatch.Template`.
"""

from aff3ct import _ext
from aff3ct._dispatch import export

__all__ = export(_ext.mnt, globals())
