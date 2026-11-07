# -*- coding: utf-8 -*-
"""Encoders.

Class templates are grouped by dtype combination (``isinstance(x, enc.<Class>)`` whatever the dtypes,
``enc.<Class>[streampu.int32]`` for one instance); see :class:`aff3ct._dispatch.Template`.
"""

from aff3ct import _ext
from aff3ct._dispatch import export, export_functions

__all__ = export(_ext.enc, globals()) + export_functions(globals(), "enc")
