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
import inspect
import shlex
import weakref
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


def _from_cli(self: Factory, args: str | Iterable[str], strict: bool = True) -> Factory:
    """Set parameters from AFF3CT command-line arguments (``"--crc-type 32-GZIP"`` or a list); return the factory.

    With ``strict=False``, the arguments of other factories are ignored: a whole AFF3CT command line can be given
    (``af.factory.Codec_polar.from_cli(cmd, strict=False)``, ``af.factory.CRC.from_cli(cmd, strict=False)``...).
    """
    if isinstance(args, str):
        args = shlex.split(args)
    args = list(args)
    _cpp_from_cli(self, args, strict)
    previous = _CLI.get(self)
    _CLI[self] = ((previous[0] if previous else []) + args, _values(self))
    return self


class _ClassOrInstanceMethod:
    """``Factory.from_cli(args, **params)`` creates a factory; ``factory.from_cli(args)`` updates this one."""

    def __init__(self, func: Callable):
        self.func = func
        functools.update_wrapper(self, func)

    def __get__(self, obj: Any, cls: type) -> Callable:
        if obj is None:

            @functools.wraps(self.func)
            def create(args: str | Iterable[str], strict: bool = True, **params: Any) -> Factory:
                return self.func(cls(**params), args, strict)

            return create
        return functools.partial(self.func, obj)


def _builders(fac: Any) -> dict[str, dict | None]:
    """Builders of a factory: {name: instantiation entry} (``None`` for a non-template builder)."""
    res: dict[str, dict | None] = dict(INSTANTIATIONS.get(_key(fac), {}).get("builders", {}))
    for name in getattr(type(fac), "_raw_builders", ()):
        res.setdefault(name, None)
    return res


def _walk(fac: Factory, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], Factory]]:
    """(path, factory) of a factory and of its sub-factories, depth first."""
    yield path, fac
    for name in dir(type(fac)):
        if name.startswith("_") or name in type(fac)._parameters or name == "parameters":
            continue
        if isinstance(inspect.getattr_static(type(fac), name, None), property):
            sub = getattr(fac, name)
            if isinstance(sub, Factory):
                yield from _walk(sub, path + (name,))


def _values(fac: Factory) -> dict[tuple[tuple[str, ...], str], Any]:
    """{(path, parameter): value} of a factory and of its sub-factories."""
    return {(path, p): getattr(f, p) for path, f in _walk(fac) for p in type(f)._parameters}


def _same(a: Any, b: Any) -> bool:
    try:
        return bool(a == b)
    except (TypeError, ValueError):  # arrays
        import numpy as np

        return bool(np.array_equal(np.asarray(a), np.asarray(b)))


# command lines given to the factories (from_cli), and the parameters right after: {factory: (args, values)}
_CLI: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()


def _complete(fac: Factory, origin: Factory | None = None) -> None:
    """Derived parameters of `fac` (a copy of `origin`), as AFF3CT computes them after the command-line parsing.

    - `origin` configured by ``from_cli``: ``store()`` with the same arguments (what AFF3CT derives from them, such as
      the frame size of a puncturer from ``-N`` or the sizes of a BCH code from ``-T``, is derived again), then the
      parameters changed since the last ``from_cli`` are set back (the command line, then the attributes).
    - otherwise: ``store()`` with an empty command line. BCH decoders: AFF3CT then derives the correction power from
      the sizes, ``t = (N - K) / m``, wrong when ``N - K < m t``: a correction power consistent with the sizes is kept.
    """
    rec = _CLI.get(origin) if origin is not None else None
    if rec is not None:
        args, after_cli = rec
        changed = {k: v for k, v in _values(origin).items() if k not in after_cli or not _same(v, after_cli[k])}
        fac._complete_cli(args)
        for (path, p), v in changed.items():
            target = fac
            for name in path:
                target = getattr(target, name)
            setattr(target, p, v)
        return
    bch = [(f, f.t) for _, f in _walk(fac) if isinstance(f, _ext.factory.Decoder_BCH)]
    fac._complete()
    for f, t in bch:
        if f.t != t and f.N_cw > f.K > 0 and t > 0:
            try:
                ok = _ext.tools.BCH_polynomial_generator_int32(f.N_cw, t).n_rdncy == f.N_cw - f.K
            except Exception:  # noqa: BLE001  (invalid t for this N: keep the derived one)
                ok = False
            if ok:
                f.t = t


def _call_builder(self: Factory, builder: str, *args: Any, **kwargs: Any) -> Any:
    """Build with the instance of `builder` selected by the dtypes given by keyword.

    The keywords that name a template parameter of the builder (``B``, ``Q``... or ``dtype``) choose the instance;
    the other ones are arguments of the builder (``crc=``, ``encoder=``...), as the positional ones. As the AFF3CT
    command line does (parse, ``store()``, then build), the derived parameters (CRC size from the polynomial, code
    rate...) are computed first, on a temporary copy: the factory keeps the values given by the user, and a derived
    value never outlives a change of the parameters it comes from.
    """
    entry = _builders(self).get(builder)
    fac = self.clone()
    _complete(fac, self)
    if entry is None:  # non-template builder
        return getattr(fac, f"_{builder}_raw")(*args, **kwargs)
    tparams = set(entry["params"]) | {"dtype"}
    dtypes = {k: v for k, v in kwargs.items() if k in tparams}
    bargs = {k: v for k, v in kwargs.items() if k not in tparams}
    combo = resolve_combo(entry, dtypes, f"{type(self).__name__}.{builder}")
    return getattr(fac, f"{builder}_{'_'.join(combo)}")(*args, **bargs)


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


def make(factory: str, builder: str, params: dict[str, Any], args: dict[str, Any], dtypes: dict[str, Any]) -> Any:
    """Engine of the generated module-level functions (``aff3ct._generated.functions``).

    Args:
        factory (str): name of the factory class in ``aff3ct.factory``.
        builder (str): builder to call (``build``, ``build_siso``...).
        params (dict): factory parameters (``None`` = AFF3CT default).
        args (dict): builder arguments by name (``None`` = C++ default, or overload without this argument).
        dtypes (dict): template dtypes (``None`` = default / only compatible value).
    """
    fac = getattr(_ext.factory, factory)(**params)
    kwargs = {k: v for k, v in args.items() if v is not None}
    kwargs.update({k: v for k, v in dtypes.items() if v is not None})
    return _call_builder(fac, builder, **kwargs)


__all__ = ["build", "make"]
