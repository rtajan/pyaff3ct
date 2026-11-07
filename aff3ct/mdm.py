# -*- coding: utf-8 -*-
"""Modems (BPSK, PAM, QAM, PSK, OOK, CPM, SCMA...).

>>> mdm = af.mdm.modem(N, type="QAM", bps=4)      # the constellation is built (and kept) for the generic types
>>> mdm = af.mdm.modem(N, af.tools.Constellation_PSK(3))

Class templates are grouped by dtype combination (``isinstance(x, mdm.<Class>)`` whatever the dtypes,
``mdm.<Class>[streampu.int32]`` for one instance); see :class:`aff3ct._dispatch.Template`.
"""

import functools
from typing import Any

from aff3ct import _ext
from aff3ct._dispatch import export, export_functions

__all__ = export(_ext.mdm, globals()) + export_functions(globals(), "mdm")

# modem types whose generic modem needs a constellation (aff3ct::factory::Modem::has_constellation)
_CONSTELLATION_TYPES = {"PSK", "PAM", "QAM", "USER"}
_generated_modem = modem  # noqa: F821  (exported above)


@functools.wraps(_generated_modem)
def modem(N: int, cstl: Any = None, dist: Any = None, **kwargs: Any) -> Any:
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


modem.__doc__ = (_generated_modem.__doc__ or "") + (
    "\n\nFor the types PSK, PAM, QAM and USER, the constellation is built from the parameters when ``cstl`` is not "
    "given (``bps``, ``const_path``); a given constellation sets the type when ``type`` is not given."
)
