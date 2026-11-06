# -*- coding: utf-8 -*-
"""AFF3CT interfaces (frozen bits, noise, trellis...), shared by modules and tools.

Class templates are grouped by dtype combination (``isinstance(x, interfaces.<Class>)`` whatever the dtypes,
``interfaces.<Class>[streampu.int32]`` for one instance); see :class:`aff3ct._dispatch.Template`.
"""

from aff3ct import _ext
from aff3ct._dispatch import export

__all__ = export(_ext.interfaces, globals())
