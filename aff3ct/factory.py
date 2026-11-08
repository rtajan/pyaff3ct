# -*- coding: utf-8 -*-
"""AFF3CT factories, for the advanced uses.

The module-level functions (``aff3ct.<sub-module>.<function>(...)``) create the modules directly: the factories
are hidden behind them. Use a factory explicitly for the command-line parity or to inspect / reuse parameters:

Examples:
    >>> f = aff3ct.factory.CRC.from_cli("--crc-type 32-GZIP --crc-implem STD")
    >>> f.K = 64
    >>> f.parameters
    >>> crc = f.build(B=streampu.int16)
"""

from aff3ct import _ext
from aff3ct._dispatch import export

__all__ = export(_ext.factory, globals(), kinds=("Factory",))
