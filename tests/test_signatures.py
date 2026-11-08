"""Signatures of the bindings without raw C++ types (``aff3ct::...``, ``<Origin.TOP_LEFT: 0>``): every type of a
signature has a Python class registered before it, so that stub generators (pybind11-stubgen) and IDEs can read them."""

import inspect
import re

import aff3ct as af
from aff3ct import _ext

RAW = re.compile(r"\w::\w|<\w+\.\w+: -?\d+>")


def _routines(module, seen):
    for name, obj in vars(module).items():
        if inspect.ismodule(obj):
            if obj.__name__.startswith("aff3ct._ext") and obj not in seen:
                seen.add(obj)
                yield from _routines(obj, seen)
        elif inspect.isclass(obj):
            for attr, member in vars(obj).items():
                if isinstance(member, property):
                    yield f"{obj.__qualname__}.{attr}", member.fget
                elif callable(member):
                    yield f"{obj.__qualname__}.{attr}", member
        elif callable(obj):
            yield name, obj


def test_no_raw_cpp_type_in_signatures():
    bad = []
    for name, f in _routines(_ext, {_ext}):
        doc = getattr(f, "__doc__", None) or ""
        # the signature lines of pybind11 (``name(args) -> ret``), not the text of the docstrings
        sigs = [line for line in doc.splitlines() if re.match(r"^(\d+\. )?\w*\(.*\) -> ", line)]
        bad += [f"{name}: {s}" for s in sigs if RAW.search(s)]
    assert not bad, "\n".join(bad[:20])


def test_sub_factory_typed():
    assert "-> aff3ct._ext.factory.Encoder" in af.factory.Codec.enc.fget.__doc__
