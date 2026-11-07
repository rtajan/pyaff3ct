# -*- coding: utf-8 -*-
"""Sources (random information bits, user data...).

The modules built here are the StreamPU sources / sinks configured by AFF3CT (``--src-*`` arguments).
"""

from aff3ct._dispatch import export_functions

__all__ = export_functions(globals(), "src")
