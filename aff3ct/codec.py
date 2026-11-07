# -*- coding: utf-8 -*-
"""Codecs: one object that builds and connects the modules of a code family (encoder, decoders, puncturer...).

>>> cdc = af.codec.polar(K, N_cw, dec_type="SCL", dec_implem="NAIVE", dec_L=8, fbg_noise=0.8)
>>> enc, dec = cdc.encoder, cdc.decoder_siho        # modules owned by the codec (they keep it alive)
>>> cdc.set_noise(af.tools.sigma_from_ebn0(2.0, K / N_cw))   # adaptive frozen bits, scaling factors...

The parameters of a codec are those of its sub-factories, prefixed by the name of the sub-factory, like the options
of the AFF3CT command line (``--dec-type`` → ``dec_type``): ``enc_*``, ``dec_*``, ``pct_*`` (puncturer),
``fbg_*`` (frozen bits generator of the polar codes), ``itl_core_*`` (interleaver of the turbo codes)...
``help(af.codec.polar)`` lists them. ``K`` and ``N_cw`` are positional; giving ``N`` (frame size) different from
``N_cw``, or a ``pct_*`` parameter, adds the puncturer. The factories stay reachable in ``aff3ct.factory``
(``af.factory.Codec_polar.from_cli("--dec-type SCL ...")``).

Class templates are grouped by dtype combination (``isinstance(x, codec.<Class>)`` whatever the dtypes,
``codec.<Class>[streampu.int32, streampu.float32]`` for one instance); see :class:`aff3ct._dispatch.Template`.
"""

from __future__ import annotations

import inspect
from typing import Any, Callable

import streampu as _spu

from aff3ct import _ext
from aff3ct._dispatch import builder_entry, export
from aff3ct._factory import _call_builder
from aff3ct._generated.functions import CODECS

Factory = _ext.factory.Factory
# sizes of the sub-factories: set from K, N_cw and N (or derived by AFF3CT), not exposed
_SIZES = {"K", "N_cw", "N", "size"}
# codecs whose K and N_cw are those of a sub-code
_SUB_CODE_SIZES = {"Codec_turbo_product"}


def _sub_factories(fac: Any) -> dict[str, Any]:
    """{name: sub-factory} of a factory (``enc``, ``dec``, ``pct``, ``itl``, ``core``...), None ones excluded."""
    res = {}
    for name in dir(type(fac)):
        if name.startswith("_") or name in type(fac)._parameters or name == "parameters":
            continue
        if not isinstance(inspect.getattr_static(type(fac), name, None), property):
            continue
        sub = getattr(fac, name)
        if isinstance(sub, Factory):
            res[name] = sub
    return res


def _prefixed_parameters(fac: Any, prefix: tuple[str, ...] = (), targets: tuple[tuple[str, ...], ...] = ((),)
                         ) -> dict[str, tuple[tuple[tuple[str, ...], ...], str, Any]]:
    """{"dec_type": ((("dec",),), "type", default)...} for every parameter of the sub-factories (recursively).

    Sibling sub-factories that share their command-line prefix (``sub1`` and ``sub2`` of a turbo encoder are both
    ``--enc-sub-*``) are set together, under the last part of that prefix (``enc_sub_standard``).
    """
    res: dict = {}
    groups: dict[str, list[str]] = {}
    subs = _sub_factories(fac)
    for name, sub in subs.items():
        groups.setdefault(sub.prefix, []).append(name)
    for cli_prefix, names in groups.items():
        sub = subs[names[0]]
        key = cli_prefix.rsplit("-", 1)[-1] if len(names) > 1 else names[0]
        sub_targets = tuple(t + (n,) for t in targets for n in names)
        for p in type(sub)._parameters:
            if p not in _SIZES:
                res["_".join(prefix + (key, p))] = (sub_targets, p, getattr(sub, p))
        res.update(_prefixed_parameters(sub, prefix + (key,), sub_targets))
    return res


def _resolve(fac: Any, path: tuple[str, ...]) -> Any:
    for name in path:
        fac = getattr(fac, name)
    return fac


def _make_function(factory_name: str, info: dict) -> Callable:
    cls = getattr(_ext.factory, factory_name)
    probe = cls()
    try:
        probe.enable_puncturer()  # factory::Codec raises when the family has no puncturer
        has_pct = probe.pct is not None
    except _spu.exceptions.RuntimeError:
        has_pct = False
    params = _prefixed_parameters(probe)
    dtypes = builder_entry(f"Factory::{factory_name}", "build")["params"]
    bargs = [a["name"] for a in info["args"]]

    def configure(K: int, N_cw: int, *args: Any, **kwargs: Any) -> tuple[Any, dict]:
        """(factory set from the arguments, builder arguments and dtypes)."""
        if len(args) > len(bargs):
            raise TypeError(f"{fname}() takes at most {2 + len(bargs)} positional arguments")
        given_bargs = dict(zip(bargs, args))
        N = kwargs.pop("N", None)
        unknown = set(kwargs) - set(params) - set(dtypes) - set(bargs) - {"dtype"}
        if unknown:
            raise TypeError(f"{fname}() got unexpected keyword argument(s) {sorted(unknown)}; see help({fname}).")
        for b in bargs:
            if b in kwargs:
                given_bargs[b] = kwargs.pop(b)
        fac = cls()
        wants_pct = (N is not None and N != N_cw) or any(k.startswith("pct_") for k in kwargs)
        if wants_pct and fac.pct is None:
            if not has_pct:
                raise TypeError(f"{fname}(): the {factory_name} codec has no puncturer (N must be N_cw).")
            fac.enable_puncturer()
        # sizes: given to the encoder and to the puncturer (AFF3CT propagates them from one or the other, depending on
        # the family); turbo product codes: sizes of the sub-code (the product code is (N_cw^2, K^2))
        size_holder = fac.enc.sub if factory_name in _SUB_CODE_SIZES else fac.enc
        size_holder.K, size_holder.N_cw = K, N_cw
        if fac.pct is not None:
            fac.pct.K, fac.pct.N_cw, fac.pct.N = K, N_cw, N if N is not None else N_cw
        for k in [k for k in kwargs if k in params]:
            value = kwargs.pop(k)
            if value is not None:
                paths, p, _ = params[k]
                for path in paths:
                    setattr(_resolve(fac, path), p, value)
        call = {k: v for k, v in given_bargs.items() if v is not None}
        call.update({k: v for k, v in kwargs.items() if v is not None})  # dtypes
        return fac, call

    def function(K: int, N_cw: int, *args: Any, **kwargs: Any) -> Any:
        fac, call = configure(K, N_cw, *args, **kwargs)
        return _call_builder(fac, "build", **call)

    def factory(K: int, N_cw: int, **kwargs: Any) -> Any:
        """The factory the codec would be built with (``print(f.headers())`` as the AFF3CT simulator)."""
        fac, _ = configure(K, N_cw, **{k: v for k, v in kwargs.items() if k not in dtypes})
        fac = fac.clone()
        fac._complete()
        return fac

    fname = info["function"]
    P = inspect.Parameter
    sig = [P("K", P.POSITIONAL_OR_KEYWORD, annotation=int), P("N_cw", P.POSITIONAL_OR_KEYWORD, annotation=int)]
    sig += [P(a["name"], P.POSITIONAL_OR_KEYWORD, default=None, annotation=Any) for a in info["args"]]
    if has_pct:
        sig.append(P("N", P.KEYWORD_ONLY, default=None, annotation=int))
    sig += [P(k, P.KEYWORD_ONLY, default=None, annotation=type(d).__name__) for k, (_, _, d) in params.items()]
    sig += [P(d, P.KEYWORD_ONLY, default=None, annotation=Any) for d in dtypes]
    function.__signature__ = inspect.Signature(sig)
    function.__name__ = function.__qualname__ = fname
    function.__module__ = __name__
    lines = [
        f"Build a {factory_name.replace('Codec_', '')} codec (``aff3ct::tools::{factory_name}<B, Q>``) with the "
        f"AFF3CT factory ``{factory_name}``.",
        "",
        "Args:",
        "    K (int): number of information bits"
        + (" of the sub-code (the product code has K^2)." if factory_name in _SUB_CODE_SIZES else "."),
        "    N_cw (int): codeword size" + (" of the sub-code (N_cw^2)." if factory_name in _SUB_CODE_SIZES else "."),
    ]
    lines += [f"    {a['name']} ({a['type']}): builder argument, default ``{a['default']}``." for a in info["args"]]
    if has_pct:
        lines.append("    N (int): frame size after puncturing (default N_cw; another value adds the puncturer).")
    lines += [f"    {k} ({type(d).__name__}): parameter ``{p}`` of the sub-factor"
              f"{'ies' if len(paths) > 1 else 'y'} {', '.join('``' + '.'.join(t) + '``' for t in paths)} "
              f"(AFF3CT default: ``{d!r}``)." for k, (paths, p, d) in params.items()]
    lines += [f"    {d} (streampu.dtype): template parameter ``{d}``." for d in dtypes]
    lines += ["", "Returns:", f"    aff3ct.codec.{factory_name}: the codec (owned by Python).", "",
              f"``{fname}.factory(...)`` (same arguments) returns the configured factory instead: its "
              "``headers()`` are "
              "those that the AFF3CT simulator prints."]
    function.__doc__ = "\n".join(lines)
    factory.__signature__ = function.__signature__
    factory.__name__ = factory.__qualname__ = f"{fname}.factory"
    function.factory = factory
    return function


FUNCTIONS = {info["function"]: _make_function(name, info) for name, info in CODECS.items()}
globals().update(FUNCTIONS)

__all__ = sorted(export(_ext.codec, globals(), kinds=("Tools",)) + list(FUNCTIONS))
