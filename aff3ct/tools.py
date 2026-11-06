# -*- coding: utf-8 -*-
"""AFF3CT tools (noise...).

Class templates are grouped by dtype combination (``isinstance(x, tools.<Class>)`` whatever the dtypes,
``tools.<Class>[streampu.int32]`` for one instance); see :class:`aff3ct._dispatch.Template`.
"""

from aff3ct import _ext
from aff3ct._dispatch import export

__all__ = export(_ext.tools, globals())
