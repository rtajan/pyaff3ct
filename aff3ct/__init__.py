# -*- coding: utf-8 -*-
"""Python interface of AFF3CT, built on pystreampu.

Every AFF3CT module is a ``streampu.Module``: its tasks are called like functions (``enc.encode(u)``), its sockets
are exposed as NumPy arrays and the chains are executed with ``streampu.Sequence`` / ``streampu.Pipeline``.
Types are the pystreampu dtypes (``streampu.int32``, ``streampu.float32``...), given with the names of the AFF3CT
template parameters (``B=``, ``R=``, ``Q=``) or with ``dtype=`` when there is a single one.

Sub-modules (same prefixes as the AFF3CT command line):

* ``crc``, ``chn``, ``cst``, ``dec``, ``enc``, ``ext``, ``mdm``, ``mnt``, ``pct``, ``qnt``, ``src``, ``snk``: modules
  and the functions that build them (``aff3ct.enc.polar(K, N_cw, frozen_bits)``, the factory being hidden);
* ``interfaces``, ``tools``: AFF3CT tools (noise, frozen bits...);
* ``factory``: AFF3CT factories, for the advanced uses (command-line parity, parameters).
"""

# streampu first: it registers the base classes of the AFF3CT modules (Module, Stateful, Task, Socket...)
import streampu as _spu  # noqa: F401  isort:skip

from aff3ct import _ext  # isort:skip
from aff3ct import _factory  # noqa: F401  (Pythonic factories)  isort:skip

from aff3ct import chn, crc, cst, dec, enc, ext, factory, interfaces, mdm, mnt, pct, qnt, snk, src, tools

try:
    from aff3ct._version import version as __version__
except ImportError:  # not installed (source tree)
    __version__ = "0.0.0"

AFF3CT_VERSION: str = _ext.AFF3CT_VERSION
"""Version of the wrapped AFF3CT library (e.g. ``v4.7.2``)."""
AFF3CT_GIT_HASH: str = _ext.AFF3CT_GIT_HASH
"""Git commit of the wrapped AFF3CT library."""

__all__ = [
    "chn",
    "crc",
    "cst",
    "dec",
    "enc",
    "ext",
    "factory",
    "interfaces",
    "mdm",
    "mnt",
    "pct",
    "qnt",
    "snk",
    "src",
    "tools",
    "AFF3CT_VERSION",
    "AFF3CT_GIT_HASH",
]
