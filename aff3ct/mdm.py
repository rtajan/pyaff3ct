# -*- coding: utf-8 -*-
"""Modems (BPSK, PAM, QAM, PSK, OOK, CPM, SCMA...).

Class templates are grouped by dtype combination (``isinstance(x, mdm.<Class>)`` whatever the dtypes,
``mdm.<Class>[streampu.int32]`` for one instance); see :class:`aff3ct._dispatch.Template`.
"""

from aff3ct import _ext
from aff3ct._dispatch import export, export_functions

__all__ = export(_ext.mdm, globals()) + export_functions(globals(), "mdm")
