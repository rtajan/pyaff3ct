# -*- coding: utf-8 -*-
"""Modems (BPSK, PAM, QAM, PSK, OOK, CPM, SCMA...).

Class templates are grouped by dtype combination (``isinstance(x, mdm.<Class>)`` whatever the dtypes,
``mdm.<Class>[streampu.int32]`` for one instance); see ``aff3ct._dispatch.Template``.

Examples:
    >>> mdm = af.mdm.modem(N, type="QAM", bps=4)      # the constellation is built (and kept) for the generic types
    >>> mdm = af.mdm.modem(N, type="USER", const_path="cstl.txt")
    >>> mdm = af.mdm.modem(N, symbols=np.exp(2j * np.pi * np.arange(8) / 8))   # any symbols, no file
    >>> mdm = af.mdm.modem(N, symbols=[-3, -1, 3, 1], bit_order="MSB")   # symbols[0b10] carries the bits 1, 0
"""

import functools
import inspect
from typing import Any

from aff3ct import _ext
from aff3ct._dispatch import export, export_functions

__all__ = export(_ext.mdm, globals()) + export_functions(globals(), "mdm")

# modem types whose generic modem needs a constellation (aff3ct::factory::Modem::has_constellation)
_CONSTELLATION_TYPES = {"PSK", "PAM", "QAM", "USER"}
_generated_modem = modem  # noqa: F821  (exported above)


@functools.wraps(_generated_modem)
def modem(N: int, cstl: Any = None, dist: Any = None, *, symbols: Any = None, bit_order: str = "LSB",
          **kwargs: Any) -> Any:
    if bit_order not in ("LSB", "MSB"):
        raise ValueError(f"modem(): bit_order must be 'LSB' or 'MSB', not {bit_order!r}")
    if symbols is not None:
        if cstl is not None:
            raise TypeError("modem(): give either cstl or symbols")
        # user constellation without file: scaled to a unit mean energy, as a constellation file
        cstl = _constellation(symbols, bit_order, R=kwargs.get("R"))
        if kwargs.get("type") == "USER":  # the factory would read const_path: the type of the given constellation
            del kwargs["type"]
    elif bit_order != "LSB":
        raise TypeError("modem(): bit_order only applies to the symbols of a user constellation (symbols=...)")
    if cstl is None and dist is None and kwargs.get("type") in _CONSTELLATION_TYPES:
        # as the AFF3CT simulator: the constellation of the parameters (the modem keeps it alive)
        cstl = modem_constellation(N, **{k: v for k, v in kwargs.items() if k not in ("B", "Q")})  # noqa: F821
    elif cstl is not None and kwargs.get("type") is None:
        # the factory builds a generic modem for a constellation type only (BPSK by default): the type of the given
        # constellation (a user one: PSK, any number of bits per symbol; the module takes its sizes from cstl)
        name = type(cstl).__name__
        kwargs["type"] = next((t for t in ("QAM", "PSK", "PAM") if f"_{t}_" in name), "PSK")
        kwargs.setdefault("bps", cstl.bps)
    return _generated_modem(N, cstl, dist, **kwargs)


def _constellation(symbols: Any, bit_order: str = "LSB", R: Any = None) -> Any:
    from aff3ct import tools

    symbols = [complex(x) for x in symbols]
    n = len(symbols)
    if bit_order == "MSB" and n > 1 and n & (n - 1) == 0:
        # AFF3CT maps the bits of i, first bit = least significant, to the symbol i: the symbol labelled i with the
        # first bit as the most significant one is the symbol AFF3CT labels with the bits of i reversed
        bps = n.bit_length() - 1
        rev = [int(format(i, f"0{bps}b")[::-1], 2) for i in range(n)]
        symbols = [symbols[rev[i]] for i in range(n)]
    return tools.Constellation(symbols, R=R)


_sig = inspect.signature(_generated_modem)
_params = list(_sig.parameters.values())
_kw = [i for i, p in enumerate(_params) if p.kind == inspect.Parameter.KEYWORD_ONLY][0]
_params[_kw:_kw] = [inspect.Parameter("symbols", inspect.Parameter.KEYWORD_ONLY, default=None, annotation=Any),
                    inspect.Parameter("bit_order", inspect.Parameter.KEYWORD_ONLY, default="LSB", annotation=str)]
modem.__signature__ = _sig.replace(parameters=_params)
modem.__doc__ = (_generated_modem.__doc__ or "") + (
    "\n\nsymbols (array-like of complex): symbols of a user constellation (2^bps of them, the symbol ``i`` being "
    "the image of the bits of ``i``), scaled to a unit mean energy: no constellation object or file is needed."
    "\n\nbit_order (str): ``'LSB'`` (default, AFF3CT convention): the first bit of a symbol is the least significant "
    "bit of its index in ``symbols``; ``'MSB'``: the most significant one (``symbols[0b100]`` carries the bits "
    "``1, 0, 0``)."
) + (
    "\n\nFor the types PSK, PAM, QAM and USER, the constellation is built from the parameters when ``cstl`` is not "
    "given (``bps``, ``const_path``); a given constellation sets the type when ``type`` is not given."
)
