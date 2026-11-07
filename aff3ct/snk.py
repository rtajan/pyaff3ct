# -*- coding: utf-8 -*-
"""Sinks (binary files, user data...).

The modules built here are the StreamPU sources / sinks configured by AFF3CT (``--snk-*`` arguments).
"""

from aff3ct._dispatch import export_functions

__all__ = export_functions(globals(), "snk")
