#!/usr/bin/env python3
"""Generate the dtype combinations available for each AFF3CT class template.

Usage:
    python3 scripts/gen_instantiations.py [docs/design/aff3ct_api.json]

Reads the API fingerprint (see aff3ct_api.py) and writes:

* ``internal/include/internal/Generated/instantiations.hpp`` : one ``pyaf::combos<pyaf::types<...>...>`` alias per
  class template (``pyaf::gen::Module_Encoder``) and per factory builder (``pyaf::gen::Factory_CRC__build``);
* ``aff3ct/_generated/instantiations.py`` : the same data for the Python dispatch (template parameter names,
  their default dtypes and the available dtype combinations).

Combinations come from the explicit instantiations of the ``AFF3CT_MULTI_PREC`` build, so every generated binding
links. Abstract bases have no explicit instantiation: they get the combinations of their descendants, propagated
through the template arguments of the inheritance (``Decoder_polar<B, R> : Decoder_SIHO<B, R>``).
"""

from __future__ import annotations

import json
import pprint
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKEN2DTYPE = {
    "B_8": "int8", "B_16": "int16", "B_32": "int32", "B_64": "int64",
    "R_8": "float32", "R_16": "float32", "R_32": "float32", "R_64": "float64",
    "Q_8": "int8", "Q_16": "int16", "Q_32": "float32", "Q_64": "float64",
    "int8_t": "int8", "int16_t": "int16", "int32_t": "int32", "int64_t": "int64",
    "uint8_t": "uint8", "uint16_t": "uint16", "uint32_t": "uint32", "uint64_t": "uint64",
    "signed char": "int8", "short": "int16", "int": "int32", "long long": "int64",
    "float": "float32", "double": "float64",
}
DTYPE2CPP = {
    "int8": "int8_t", "int16": "int16_t", "int32": "int32_t", "int64": "int64_t",
    "uint8": "uint8_t", "uint16": "uint16_t", "uint32": "uint32_t", "uint64": "uint64_t",
    "float32": "float", "float64": "double",
}


def split_top(s: str) -> list[str]:
    out, depth, cur = [], 0, ""
    for ch in s:
        depth += ch in "<("
        depth -= ch in ">)"
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return out


def type_params(tpl: list[str]) -> list[tuple[str, str | None]]:
    """['typename B = int', 'typename Q = R', 'class API = ...'] -> [('B', 'int'), ('Q', 'R')] (typename only)."""
    res = []
    for p in tpl:
        m = re.match(r"typename\s+(\w+)\s*(?:=\s*(.+))?$", p)
        if not m:
            break  # policy / non-type parameters are always trailing: not exposed
        res.append((m.group(1), m.group(2)))
    return res


def to_dtypes(args: list[str], n: int) -> tuple[str, ...] | None:
    vals = []
    for a in args[:n]:
        d = TOKEN2DTYPE.get(a.strip())
        if d is None:
            return None
        vals.append(d)
    return tuple(vals) if len(vals) == n else None


def compute(api: dict) -> dict[str, dict]:
    classes = api["classes"]
    res: dict[str, dict] = {}
    combos: dict[str, set] = defaultdict(set)
    params = {k: type_params(v["tpl"]) for k, v in classes.items()}
    builders: dict[str, dict[str, set]] = defaultdict(lambda: defaultdict(set))

    for key, v in classes.items():
        for inst in v.get("instantiations", []):
            m = re.match(r"(build\w*)<(.*)>$", inst)
            if m:  # factory builder
                builders[key][m.group(1)].add(tuple(TOKEN2DTYPE.get(a, a) for a in split_top(m.group(2))))
            elif params[key]:
                d = to_dtypes(split_top(inst), len(params[key]))
                if d:
                    combos[key].add(d)

    # header-only class templates (module::Interleaver<D, T>) have no explicit instantiation: they get the
    # combinations of the factory builders that return them (template<typename D> module::Interleaver<D>* build)
    for key, v in classes.items():
        for meth in v.get("methods", []):
            mm = re.match(r"template<(.*?)>\s*(?:static\s+)?(?:const\s+)?(?:aff3ct::)?(module|tools)::(\w+)<(.*?)>\*\s*"
                          r"(build\w*)\(", meth)
            if not mm or mm.group(5) not in builders.get(key, {}):
                continue
            ckey = f"{'Module' if mm.group(2) == 'module' else 'Tools'}::{mm.group(3)}"
            if ckey not in classes or combos[ckey] or not params[ckey]:
                continue
            bnames = [p for p, _ in type_params(split_top(mm.group(1)))]
            rargs = split_top(mm.group(4))
            cparams = params[ckey]
            for bc in builders[key][mm.group(5)]:
                env = dict(zip(bnames, bc))
                c = []
                for i, (p, d) in enumerate(cparams):
                    a = rargs[i] if i < len(rargs) else d  # template argument, else the class default
                    c.append(env.get(a) or TOKEN2DTYPE.get(a or ""))
                if None not in c:
                    combos[ckey].add(tuple(c))
    # propagate combinations to the bases, following the template arguments of the inheritance
    changed = True
    while changed:
        changed = False
        for key, v in classes.items():
            kind = key.split("::")[0]
            names = [p for p, _ in params[key]]
            for b in v["bases"]:
                m = re.match(r"(?:\w+::)*(\w+)\s*<(.*)>$", b)
                if not m:
                    continue
                bkey = f"{kind}::{m.group(1)}"
                if bkey not in classes or not params[bkey]:
                    continue
                bargs = split_top(m.group(2))[: len(params[bkey])]
                for c in list(combos[key]):
                    env = dict(zip(names, c))
                    bc = tuple(env.get(a) or TOKEN2DTYPE.get(a) for a in bargs)
                    if None not in bc and len(bc) == len(params[bkey]) and bc not in combos[bkey]:
                        combos[bkey].add(bc)
                        changed = True

    # header-only tool templates never instantiated explicitly (Constellation_QAM<R> : Constellation<R>): the
    # combinations of their base when they forward their parameters to it unchanged
    for key, v in classes.items():
        if not key.startswith("Tools::") or combos[key] or not params[key]:
            continue
        names = [p for p, _ in params[key]]
        for b in v["bases"]:
            m = re.match(r"(?:\w+::)*(\w+)\s*<(.*)>$", b)
            bkey = f"Tools::{m.group(1)}" if m else None
            if bkey in classes and [a.strip() for a in split_top(m.group(2))] == names and combos[bkey]:
                combos[key] = set(combos[bkey])
                break

    # factory class templates (Decoder_turbo<>): their builders are implemented in headers, without explicit
    # instantiation; they get the combinations of the module class they return (module::Decoder_turbo<B, Q>)
    for key, v in classes.items():
        if not key.startswith("Factory::") or not v["tpl"]:
            continue
        for meth in v.get("methods", []):
            mm = re.match(r"template<(.*?)>\s*(?:const\s+)?(?:aff3ct::)?module::(\w+)<(.*?)>\*\s*(build\w*)\(", meth)
            if not mm or builders.get(key, {}).get(mm.group(4)):
                continue
            bnames = [p for p, _ in type_params(split_top(mm.group(1)))]
            mkey = f"Module::{mm.group(2)}"
            margs = [a.strip() for a in split_top(mm.group(3))]
            if margs != bnames or len(params.get(mkey, [])) < len(bnames):  # Decoder_turbo<B, Q> -> module<B, R>
                continue
            for c in combos.get(mkey, ()):
                builders[key][mm.group(4)].add(tuple(c[: len(bnames)]))
    for key in classes:
        if params[key] and combos[key]:
            res[key] = {
                "params": [p for p, _ in params[key]],
                "defaults": [d for _, d in params[key]],
                "combos": sorted(combos[key], key=lambda c: [list(DTYPE2CPP).index(x) for x in c]),
            }
        if key in builders:
            res.setdefault(key, {})["builders"] = {
                b: sorted(cs, key=lambda c: [list(DTYPE2CPP).index(x) if x in DTYPE2CPP else 99 for x in c])
                for b, cs in builders[key].items()
            }
    return res


# Default dtypes of the AFF3CT precision parameters: those of the 32-bit precision of the command line
# (B_32 = int32, R_32 = Q_32 = float32). The C++ defaults may name a combination that the MULTI_PREC build does not
# compile (e.g. Quantizer<R = float, Q = int>), whereas the 32-bit group always is.
PRECISION_32 = {"B": "int32", "R": "float32", "Q": "float32"}


def default_dtypes(params: list[str], defaults: list[str | None]) -> list[str | None]:
    """Default dtype of each template parameter; a parameter name (e.g. Q = R) means 'same as this parameter'."""
    res = []
    for p, d in zip(params, defaults):
        if d is not None and d in params:
            res.append(d)  # Q = R: same dtype as R
        elif p in PRECISION_32:
            res.append(PRECISION_32[p])
        else:
            res.append(None if d is None else TOKEN2DTYPE.get(d))
    return res


def builder_params(api: dict, key: str, builder: str) -> tuple[list[str], list[str | None]]:
    """Template parameters of a factory builder, from its signature ('template<typename B = int, ...>...build(')."""
    for m in api["classes"][key].get("methods", []):
        mm = re.match(r"template<(.*?)>.*?\b" + builder + r"\(", m)
        if mm:
            ps = type_params(split_top(mm.group(1)))
            return [p for p, _ in ps], default_dtypes([p for p, _ in ps], [d for _, d in ps])
    return [], []


def cpp_ident(key: str) -> str:
    return key.replace("::", "_")


def main() -> None:
    api_file = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "docs/design/aff3ct_api.json"
    api = json.loads(api_file.read_text())
    data = compute(api)
    meta = api["meta"]
    head = f"AFF3CT {meta['describe']} ({meta['commit'][:10]})"

    hpp = [
        "// Generated by scripts/gen_instantiations.py from docs/design/aff3ct_api.json: do not edit.",
        f"// {head}",
        "#ifndef PYAF_GENERATED_INSTANTIATIONS_HPP_",
        "#define PYAF_GENERATED_INSTANTIATIONS_HPP_",
        "",
        "#include <cstdint>",
        "",
        '#include "internal/Common/Tools/combos.hpp"',
        "",
        "namespace pyaf",
        "{",
        "namespace gen",
        "{",
    ]
    for key in sorted(data):
        d = data[key]
        if "combos" in d:
            cs = ", ".join("types<" + ", ".join(DTYPE2CPP[x] for x in c) + ">" for c in d["combos"])
            hpp.append(f"using {cpp_ident(key)} = combos<{cs}>;")
        for b, combos in sorted(d.get("builders", {}).items()):
            if all(all(x in DTYPE2CPP for x in c) for c in combos):
                cs = ", ".join("types<" + ", ".join(DTYPE2CPP[x] for x in c) + ">" for c in combos)
                hpp.append(f"using {cpp_ident(key)}__{b} = combos<{cs}>;")
    hpp += ["} // namespace gen", "} // namespace pyaf", "", "#endif // PYAF_GENERATED_INSTANTIATIONS_HPP_", ""]
    out_hpp = ROOT / "internal/include/internal/Generated/instantiations.hpp"
    out_hpp.parent.mkdir(parents=True, exist_ok=True)
    out_hpp.write_text("\n".join(hpp))

    py = {}
    for key, d in sorted(data.items()):
        entry = {}
        if "combos" in d:
            entry.update(params=d["params"], defaults=default_dtypes(d["params"], d["defaults"]),
                         combos=[list(c) for c in d["combos"]])
        if "builders" in d:
            entry["builders"] = {}
            for b, cs in d["builders"].items():
                names, defaults = builder_params(api, key, b)
                entry["builders"][b] = {"params": names, "defaults": defaults, "combos": [list(c) for c in cs]}
        py[key] = entry
    out_py = ROOT / "aff3ct/_generated/instantiations.py"
    out_py.parent.mkdir(parents=True, exist_ok=True)
    (out_py.parent / "__init__.py").write_text('"""Code generated from the AFF3CT API fingerprint: do not edit."""\n')
    out_py.write_text(
        f'"""dtype combinations compiled by AFF3CT ({head}).\n\n'
        'Generated by scripts/gen_instantiations.py: do not edit.\n"""\n\n'
        f"AFF3CT_VERSION = {meta['describe']!r}\nAFF3CT_COMMIT = {meta['commit']!r}\n\n"
        f"INSTANTIATIONS = {pprint.pformat(py, width=120, sort_dicts=True)}\n"
    )
    n_cls = sum("combos" in d for d in data.values())
    n_bld = sum(len(d.get("builders", {})) for d in data.values())
    print(f"{n_cls} class templates, {n_bld} factory builders -> {out_hpp.relative_to(ROOT)}, {out_py.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
