# -*- coding: utf-8 -*-
"""Resolution of the pystreampu dtypes to the C++ instances compiled by AFF3CT.

pyaff3ct defines no dtype: template parameters are given with the pystreampu dtypes (``spu.int32``,
``spu.float32``...) under the names of the AFF3CT template parameters (``B``, ``R``, ``Q``...), or with ``dtype=``
when the template has a single parameter. The available combinations are generated from the AFF3CT explicit
instantiations (``aff3ct/_generated/instantiations.py``).
"""

from __future__ import annotations

import inspect
import re
from typing import Any, Iterable, Mapping

import streampu as spu

from aff3ct._generated.instantiations import INSTANTIATIONS


def _name(dt: Any, param: str) -> str:
    if not isinstance(dt, spu.dtype):
        raise TypeError(f"'{param}' must be a streampu dtype (e.g. streampu.int32), not {type(dt).__name__!r}.")
    return dt.name


def _fmt(params: list[str], combo: Iterable[str]) -> str:
    return ", ".join(f"{p}={c}" for p, c in zip(params, combo))


def resolve_combo(entry: Mapping[str, Any], dtypes: Mapping[str, Any], what: str) -> tuple[str, ...]:
    """Return the dtype names of the combination selected by `dtypes`.

    The given dtypes are kept as is. Each missing parameter takes the only value compatible with the given ones
    when there is a single one (``Decoder_SIHO`` with ``B=int8`` → ``R=int8``), its default otherwise (``B=int32``,
    ``R=Q=float32``, the 32-bit precision of AFF3CT; ``Q=R`` when the C++ template says so).

    Args:
        entry (dict): {"params": [...], "defaults": [...], "combos": [[...], ...]} (generated).
        dtypes (dict): given dtypes, by template parameter name; ``dtype`` stands for the single parameter.
        what (str): name used in the error messages.

    Raises:
        TypeError: unknown parameter, value that is not a streampu dtype, combination not compiled by AFF3CT or
            ambiguous (the available combinations are listed).
    """
    params, defaults = list(entry["params"]), list(entry["defaults"])
    combos = [tuple(c) for c in entry["combos"]]
    given = {k: v for k, v in dtypes.items() if v is not None}
    if "dtype" in given:
        if len(params) != 1:
            raise TypeError(f"{what} has several template parameters ({', '.join(params)}): use them instead of 'dtype'.")
        given[params[0]] = given.pop("dtype")
    unknown = set(given) - set(params)
    if unknown:
        raise TypeError(f"{what}: unknown template parameter(s) {sorted(unknown)}; valid: {params}.")
    chosen = {p: _name(v, p) for p, v in given.items()}
    avail = "; ".join(_fmt(params, c) for c in combos)

    def compatible() -> list[tuple[str, ...]]:
        return [c for c in combos if all(c[params.index(p)] == d for p, d in chosen.items())]

    cands = compatible()
    if not cands:
        raise TypeError(f"{what} is not compiled for ({_fmt(list(chosen), chosen.values())}). Available: {avail}.")
    for i, p in enumerate(params):
        if p in chosen:
            continue
        values = {c[i] for c in cands}
        if len(values) == 1:
            chosen[p] = values.pop()
        else:
            d = defaults[i]
            d = chosen.get(d, d) if d in params else d  # Q = R
            if d is None or d not in values:
                raise TypeError(
                    f"{what}: give the template parameter '{p}' (possible values here: {sorted(values)}). "
                    f"Available: {avail}."
                )
            chosen[p] = d
        cands = compatible()
    return tuple(chosen[p] for p in params)


# class templates of pyaff3ct itself (internal/include/internal/Module): same dtype combinations as an AFF3CT class
PYAFF3CT_TEMPLATES = {
    "Module::Monitor_BFER_AR": "Module::Monitor_BFER",
    "Tools::Histogram": "Tools::Distribution",  # header-only in AFF3CT: bound for the same R (float32, float64)
}


def _known(key: str) -> bool:
    return key in INSTANTIATIONS or key in PYAFF3CT_TEMPLATES


def class_entry(key: str) -> dict:
    """Generated entry of a class template (``"Module::Encoder"``)."""
    try:
        entry = INSTANTIATIONS[PYAFF3CT_TEMPLATES.get(key, key)]
    except KeyError:
        raise KeyError(f"no dtype combination known for {key!r}") from None
    if "combos" not in entry:
        raise KeyError(f"{key!r} is not a class template")
    return entry


def builder_entry(key: str, builder: str) -> dict:
    """Generated entry of a factory builder (``"Factory::CRC"``, ``"build"``)."""
    return INSTANTIATIONS[key]["builders"][builder]


class Template:
    """Python view of an AFF3CT class template: groups the C++ instances compiled for each dtype combination.

    >>> af.enc.Encoder[spu.int32]          # the class of the int32 instance
    >>> isinstance(enc, af.enc.Encoder)    # True whatever the dtypes of enc
    >>> af.dec.Decoder_SIHO[spu.int16, spu.int16]
    """

    def __init__(self, key: str, scope: Any, name: str | None = None):
        self._key = key
        self._scope = scope
        self.__name__ = name or key.split("::")[-1]
        self.__qualname__ = self.__name__
        self.__doc__ = f"AFF3CT class template {key.split('::')[-1]}<{', '.join(class_entry(key)['params'])}>."

    @property
    def params(self) -> list[str]:
        """Names of the template parameters (B, R, Q...)."""
        return list(class_entry(self._key)["params"])

    @property
    def instances(self) -> dict[tuple[str, ...], type]:
        """{dtype names: class} for every combination compiled by AFF3CT."""
        res = {}
        for c in class_entry(self._key)["combos"]:
            cls = getattr(self._scope, f"{self.__name__}_{'_'.join(c)}", None)
            if cls is not None:
                res[tuple(c)] = cls
        return res

    def resolve(self, **dtypes: Any) -> type:
        """Class of the instance selected by the dtypes (``B=spu.int32``... or ``dtype=``), defaults included."""
        combo = resolve_combo(class_entry(self._key), dtypes, self.__name__)
        return getattr(self._scope, f"{self.__name__}_{'_'.join(combo)}")

    def __getitem__(self, dtypes: Any) -> type:
        if not isinstance(dtypes, tuple):
            dtypes = (dtypes,)
        params = self.params
        if len(dtypes) > len(params):
            raise TypeError(f"{self.__name__} has {len(params)} template parameter(s): {params}.")
        return self.resolve(**dict(zip(params, dtypes)))

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Build an instance: the keywords named after the template parameters (or ``dtype``) select the dtypes.

        >>> af.tools.Sigma(0.5)                       # R = float32 (default)
        >>> af.tools.Sigma(0.5, R=spu.float64)
        >>> af.itl.Interleaver(core, D=spu.float32)
        """
        names = set(self.params) | {"dtype"}
        dtypes = {k: kwargs.pop(k) for k in list(kwargs) if k in names}
        return self.resolve(**dtypes)(*args, **kwargs)

    def __instancecheck__(self, obj: Any) -> bool:
        return any(isinstance(obj, cls) for cls in self.instances.values())

    def __subclasscheck__(self, cls: type) -> bool:
        return any(issubclass(cls, c) for c in self.instances.values())

    def __repr__(self) -> str:
        return f"<aff3ct template {self.__name__}<{', '.join(self.params)}>>"


_DTYPE = r"(?:u?int(?:8|16|32|64)|float(?:32|64))"
_INSTANCE_RE = re.compile(rf"^(?P<base>[A-Za-z]\w*?)_(?P<dtypes>{_DTYPE}(?:_{_DTYPE})*)$")


def export(scope: Any, namespace: dict, kinds: Iterable[str] = ("Module", "Tools")) -> list[str]:
    """Export the classes of a sub-module of ``aff3ct._ext`` into a Python module namespace.

    The instances of a class template (``Encoder_int8`` ... ``Encoder_int64``) are grouped into one
    :class:`Template` (``Encoder``); the other classes, enums and functions are exported as is. The instances stay
    reachable in ``aff3ct._ext`` only, which keeps the public namespace small.

    Returns:
        out (list[str]): exported names (for ``__all__``).
    """
    names = []
    groups: dict[str, list[str]] = {}
    for name in dir(scope):
        if name.startswith("_"):
            continue
        m = _INSTANCE_RE.match(name)
        if m:
            groups.setdefault(m.group("base"), []).append(name)
        elif isinstance(getattr(scope, name), type) or inspect.isbuiltin(getattr(scope, name)):
            namespace[name] = getattr(scope, name)
            names.append(name)
    for base in groups:
        key = next((f"{k}::{base}" for k in kinds if _known(f"{k}::{base}")), None)
        if key is None:  # not a template known by the generator: keep the instances
            for name in groups[base]:
                namespace[name] = getattr(scope, name)
                names.append(name)
            continue
        namespace[base] = Template(key, scope, base)
        names.append(base)
    return sorted(names)


def export_functions(namespace: dict, module: str) -> list[str]:
    """Export the generated module-level functions of a sub-module (``aff3ct._generated.functions``).

    Returns:
        out (list[str]): exported names (for ``__all__``).
    """
    from aff3ct._generated.functions import FUNCTIONS

    names = []
    for name, func in FUNCTIONS.get(module, {}).items():
        func.__name__ = func.__qualname__ = name
        func.__module__ = f"aff3ct.{module}"
        namespace[name] = func
        names.append(name)
    return sorted(names)


__all__ = ["Template", "resolve_combo", "class_entry", "builder_entry", "export", "export_functions"]
