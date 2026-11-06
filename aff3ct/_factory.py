# -*- coding: utf-8 -*-
"""Transparent factories (Plan.md, rule R5).

The module-level functions (``aff3ct.crc.polynomial(K, "32-GZIP")``) call :func:`build`: it creates the AFF3CT
factory, sets the parameters given by keyword, then calls the builder instantiated for the requested pystreampu
dtypes. The user gets the module directly and never handles the factory.

For the advanced uses, the factories of ``aff3ct.factory`` get a Pythonic interface here:

>>> fac = aff3ct.factory.CRC(K=64, type="32-GZIP")      # keyword parameters
>>> fac = aff3ct.factory.CRC.from_cli("--crc-type 32-GZIP --crc-implem STD", K=64)  # command-line parity
>>> fac.from_cli("--crc-implem FAST")                    # update an existing factory
>>> fac.parameters                                       # {'K': 64, 'type': '32-GZIP', 'implem': 'STD', ...}
>>> crc = fac.build(dtype=spu.int16)                     # builder chosen from the dtypes
"""

from __future__ import annotations

import functools
import shlex
from typing import Any, Callable, Iterable

from aff3ct import _ext
from aff3ct._dispatch import builder_entry, resolve_combo
from aff3ct._generated.instantiations import INSTANTIATIONS

Factory = _ext.factory.Factory
_cpp_from_cli = Factory.from_cli  # C++ implementation (list of arguments), wrapped below


def _key(fac: Any) -> str:
    return f"Factory::{type(fac).__name__}"


def _set(self: Factory, **params: Any) -> Factory:
    """Set parameters by keyword (``None`` keeps the current value); return the factory.

    Raises:
        TypeError: if a parameter does not exist (the valid ones are listed).
    """
    valid = type(self)._parameters
    unknown = [k for k in params if k not in valid]
    if unknown:
        raise TypeError(
            f"unknown parameter(s) {unknown} for the factory {type(self).__name__}; valid parameters: {list(valid)}."
        )
    for k, v in params.items():
        if v is not None:
            setattr(self, k, v)
    return self


def _parameters(self: Factory) -> dict[str, Any]:
    """Current value of every parameter of the factory."""
    return {k: getattr(self, k) for k in type(self)._parameters}


def _repr(self: Factory) -> str:
    return f"{type(self).__name__}({', '.join(f'{k}={v!r}' for k, v in _parameters(self).items())})"


def _from_cli(self: Factory, args: str | Iterable[str]) -> Factory:
    """Set parameters from AFF3CT command-line arguments (``"--crc-type 32-GZIP"`` or a list); return the factory."""
    if isinstance(args, str):
        args = shlex.split(args)
    _cpp_from_cli(self, list(args))
    return self


class _ClassOrInstanceMethod:
    """``Factory.from_cli(args, **params)`` creates a factory; ``factory.from_cli(args)`` updates this one."""

    def __init__(self, func: Callable):
        self.func = func
        functools.update_wrapper(self, func)

    def __get__(self, obj: Any, cls: type) -> Callable:
        if obj is None:

            @functools.wraps(self.func)
            def create(args: str | Iterable[str], **params: Any) -> Factory:
                return self.func(cls(**params), args)

            return create
        return functools.partial(self.func, obj)


def _builders(fac: Any) -> dict[str, dict]:
    return INSTANTIATIONS.get(_key(fac), {}).get("builders", {})


def _call_builder(self: Factory, builder: str, *args: Any, **dtypes: Any) -> Any:
    """Build with the instance of `builder` selected by `dtypes`.

    As the AFF3CT command line does (parse, ``store()``, then build), the derived parameters (CRC size from the
    polynomial, code rate...) are computed first, on a temporary copy: the factory keeps the values given by the
    user, and a derived value never outlives a change of the parameters it comes from.
    """
    entry = builder_entry(_key(self), builder)
    combo = resolve_combo(entry, dtypes, f"{type(self).__name__}.{builder}")
    fac = self.clone()
    fac._complete()
    return getattr(fac, f"{builder}_{'_'.join(combo)}")(*args)


def _getattr(self: Factory, name: str) -> Callable:
    # `fac.build(...)`, `fac.build_siso(...)`: builders dispatched on the dtypes given by keyword
    if name in _builders(self):
        return functools.partial(_call_builder, self, name)
    raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")


def _dir(self: Factory) -> list[str]:
    return sorted(set(object.__dir__(self)) | set(_builders(self)))


def _patch_init(cls: type) -> None:
    """Accept the parameters by keyword in the constructor: ``CRC(K=64, type="32-GZIP")``."""
    init = cls.__init__

    @functools.wraps(init)
    def __init__(self: Any, *args: Any, **params: Any) -> None:
        init(self, *args)
        _set(self, **params)

    cls.__init__ = __init__


Factory.set = _set
Factory.parameters = property(_parameters)
Factory.__repr__ = _repr
Factory.from_cli = _ClassOrInstanceMethod(_from_cli)
Factory.__getattr__ = _getattr
Factory.__dir__ = _dir
for _cls in vars(_ext.factory).values():
    if isinstance(_cls, type) and issubclass(_cls, Factory) and _cls is not Factory:
        _patch_init(_cls)


def build(factory_cls: type, params: dict[str, Any], dtypes: dict[str, Any], *args: Any, builder: str = "build") -> Any:
    """Create `factory_cls`, set `params` (``None`` = factory default), call `builder` with `args` for the dtypes.

    This is the engine of the module-level functions: the factory is a temporary, only the module is returned.
    """
    fac = factory_cls(**params)
    return _call_builder(fac, builder, *args, **dtypes)


__all__ = ["build"]
