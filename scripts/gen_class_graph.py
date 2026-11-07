#!/usr/bin/env python3
"""Generate the wrapping class graph and inventory of pyaff3ct from the AFF3CT headers.

Usage:
    python3 scripts/gen_class_graph.py <path/to/aff3ct/include> docs/design

The script parses every ``*.hpp`` of ``include/Module``, ``include/Tools`` and
``include/Factory``, extracts the class declarations and their base classes,
then classifies each class with the rules of ``Plan.md`` (section "Stratégie
de wrapping"). It writes:

* ``class_graph.md``   : Mermaid graphs (one per domain) + "uses" dependencies.
* ``inventory.md``     : one row per class with strategy / priority / Python name.
* ``inventory.json``   : same data, machine readable (used to track progress).
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# --------------------------------------------------------------------------------------------- parsing helpers

CLS_RE = re.compile(
    r"(template\s*<(?P<tpl>[^{;]*?)>\s*)?"
    r"(?<!enum )(class|struct)\s+(?P<name>[A-Za-z_]\w*)\s*(final\s*)?"
    r"(:\s*(?P<bases>[^{;]*))?\{",
    re.S,
)
MSVC_RE = re.compile(r"#ifdef _MSC_VER\s*\n.*?#else\s*\n(.*?)#endif", re.S)
CTOR_TYPES_RE = re.compile(r"\b(?:(?:spu::)?(?:tools|module)::)?([A-Z]\w+)\s*(?:<[^<>]*(?:<[^<>]*>[^<>]*)*>)?\s*[&*]")


def strip(txt: str) -> str:
    # one pass: a "//" inside a block comment (/* http://... */) must not hide its end, and conversely
    txt = re.sub(r"/\*.*?\*/|//[^\n]*", "", txt, flags=re.S)
    return MSVC_RE.sub(r"\1", txt)


def split_top(s: str) -> list[str]:
    out, depth, cur = [], 0, ""
    for ch in s:
        depth += ch == "<"
        depth -= ch == ">"
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return [" ".join(x.split()) for x in out if x.strip()]


def parse(root: Path, kind: str) -> list[dict]:
    res = []
    for f in sorted((root / kind).rglob("*.hpp")):
        txt = strip(f.read_text(errors="ignore"))
        for m in CLS_RE.finditer(txt):
            bases = [re.sub(r"^(public|protected|private|virtual)\s+", "", b) for b in split_top(m.group("bases") or "")]
            tpl = split_top(m.group("tpl") or "")
            name = m.group("name")
            # constructor signatures -> referenced classes ("uses" edges)
            uses = set()
            for c in re.finditer(r"\b" + name + r"\s*\(([^;{]*?)\)\s*[;:{]", txt):
                uses |= set(CTOR_TYPES_RE.findall(c.group(1)))
            if kind == "Factory":
                for c in re.finditer(r"\bbuild\w*\s*\(([^;{]*?)\)\s*const", txt):
                    uses |= set(CTOR_TYPES_RE.findall(c.group(1)))
            uses.discard(name)
            res.append(
                {
                    "kind": kind,
                    "file": str(f.relative_to(root)),
                    "name": name,
                    "tpl": tpl,
                    "bases": bases,
                    "uses": sorted(uses),
                }
            )
    return res


# --------------------------------------------------------------------------------------------- classification

# Classes already wrapped by pystreampu: they are *imported* (py::module_::import("streampu")), never re-wrapped.
SPU = {
    "Module", "Stateful", "Stateless", "Task", "Socket", "Source", "Sink", "Reporter", "Terminal",
    "Interface_set_seed", "Interface_reset", "Interface_is_done", "Interface_clone",
    "Interface_get_set_n_frames", "Interface_waiting",
}

# Python sub-module (= AFF3CT factory prefix) per module domain.
PREFIX = {
    "CRC": "crc", "Channel": "chn", "Coset": "cst", "Decoder": "dec", "Encoder": "enc", "Extractor": "ext",
    "Interleaver": "itl", "Modem": "mdm", "Monitor": "mnt", "Puncturer": "pct", "Quantizer": "qnt", "Source": "src",
}

# Abstract module bases: bound without constructor (tasks, sockets and accessors are inherited by every child).
ABSTRACT_MODULES = {
    "CRC", "Channel", "Coset", "Decoder", "Decoder_HIHO", "Decoder_SIHO", "Decoder_SISO", "Encoder", "Extractor",
    "Modem", "Monitor", "Puncturer", "Quantizer",
}

# Template-policy classes needed for the first end-to-end chains (only reachable through their factory).
P0_FACTORY_ONLY = {
    "Decoder_polar_SC_fast_sys", "Decoder_polar_SC_naive", "Decoder_polar_SC_naive_sys",
    "Decoder_LDPC_BP_flooding_SPA", "Decoder_LDPC_BP_horizontal_layered",
}

# Advanced / niche module families (wrapped after the core coverage).
P2_MODULES = re.compile(
    r"Optical|optical|/User/|_user|SCMA|CPM|Polar_MK|Polar_PAC|Polar_PT|EXIT|/MI/|Coset|Turbo_product|AZCW|"
    r"Viterbi_list|_AVX|_SSE|json|Genius|genius|DVBS2|bitpacked"
)

# Factories needed by the first end-to-end chains.
P0_FACTORIES = {
    "Factory", "CRC", "Channel", "Encoder", "Encoder_NO", "Encoder_polar", "Encoder_LDPC", "Encoder_BCH", "Encoder_RS",
    "Encoder_repetition", "Decoder", "Decoder_NO", "Decoder_polar", "Decoder_LDPC", "Decoder_BCH", "Decoder_RS",
    "Decoder_repetition", "Modem", "Quantizer", "Monitor", "Monitor_BFER", "Source", "Sink", "Interleaver",
    "Interleaver_core", "Puncturer", "Frozenbits_generator", "Noise", "Terminal",
}

# Factory in charge of each module family folder (Module/<Domain>/<Family>/...).
FAMILY_FACTORY = {
    "Polar": "Decoder_polar", "Polar_MK": "Decoder_polar_MK", "Polar_PAC": "Decoder_polar_PAC",
    "Polar_PT": "Decoder_polar_PT", "LDPC": "Decoder_LDPC", "RSC": "Decoder_RSC", "RSC_DB": "Decoder_RSC_DB",
    "Conv": "Decoder_conv", "Turbo": "Decoder_turbo", "Turbo_DB": "Decoder_turbo_DB",
    "Turbo_product": "Decoder_turbo_product", "Generic": "Decoder", "BCH": "Decoder_BCH", "RS": "Decoder_RS",
}


def factory_for(c: dict) -> str:
    parts = Path(c["file"]).parts
    if c["domain"] == "Decoder" and len(parts) > 3:
        return FAMILY_FACTORY.get(parts[2], "Decoder")
    return c["domain"]


# Internal helper structs that are never exposed.
INTERNAL = re.compile(r"^(Contents_\w+|Attributes|info|Tree_node_info|tsk|sck)$")

# Tools: explicit decisions (name regex -> (strategy, priority, python sub-module)).
#   wrap    : bound with pybind11, constructor(s) exposed
#   abstract: bound without constructor (base class / interface, for downcast & polymorphism)
#   factory : reachable only through an AFF3CT factory (heavy template meta-programming)
#   func    : free functions to expose
#   skip    : internal implementation detail, not exposed
TOOLS_RULES = [
    (r"^Interface_(get_set_frozen_bits|get_set_noise|notify_noise_update)$", "abstract", "P0", "interfaces"),
    (r"^Interface_\w+$", "abstract", "P1", "interfaces"),
    (r"^(Noise)$", "abstract", "P0", "tools"),
    (r"^(Sigma)$", "wrap", "P0", "tools"),
    (r"^(Event_probability|Received_optical_power)$", "wrap", "P1", "tools"),
    (r"^(Matrix)$", "abstract", "P0", "tools"),
    (r"^(Sparse_matrix)$", "wrap", "P0", "tools"),
    (r"^(Full_matrix)$", "wrap", "P1", "tools"),
    (r"^(AList|QC|LDPC_matrix_handler)$", "func", "P1", "tools.ldpc"),
    (r"^(Galois)$", "abstract", "P0", "tools"),
    (r"^(BCH_polynomial_generator|RS_polynomial_generator)$", "wrap", "P0", "tools"),
    (r"^(Polar_code)$", "wrap", "P1", "tools.polar"),
    (r"^Frozenbits_generator$", "abstract", "P0", "tools.polar"),
    (r"^Frozenbits_generator_(GA_Arikan|BEC|file)$", "wrap", "P0", "tools.polar"),
    (r"^Frozenbits_generator_\w+$", "wrap", "P1", "tools.polar"),
    (r"^Pretransform_generator$", "abstract", "P1", "tools.polar"),
    (r"^Pretransform_generator_\w+$", "wrap", "P1", "tools.polar"),
    (r"^Interleaver_core$", "abstract", "P0", "tools.itl"),
    (r"^Interleaver_core_(NO|random|LTE|user)$", "wrap", "P0", "tools.itl"),
    (r"^Interleaver_core_\w+$", "wrap", "P1", "tools.itl"),
    (r"^Constellation$", "abstract", "P1", "tools.cst"),
    (r"^Constellation_\w+$", "wrap", "P1", "tools.cst"),
    (r"^(Distribution|Distributions)$", "wrap", "P1", "tools"),
    (r"^Draw_generator$", "abstract", "P1", "tools.gen"),
    (r"^(Gaussian_noise_generator|Event_generator|User_pdf_noise_generator)$", "abstract", "P1", "tools.gen"),
    (r"^(Gaussian_noise_generator|Event_generator|User_pdf_noise_generator)_(std|fast)$", "wrap", "P1", "tools.gen"),
    (r"^(Gaussian_noise_generator|Event_generator|User_pdf_noise_generator)_(GSL|MKL)$", "wrap", "P3", "tools.gen"),
    (r"^Post_processing_SISO$", "abstract", "P1", "tools.turbo"),
    (r"^(CRC_checker|CRC_checker_DB|Flip_and_check|Flip_and_check_DB|Self_corrected|Scaling_factor)$", "wrap", "P1", "tools.turbo"),
    (r"^Scaling_factor_\w+$", "wrap", "P1", "tools.turbo"),
    (r"^Codec$", "abstract", "P1", "codec"),
    (r"^Codec_(HIHO|SIHO|SISO)$", "abstract", "P1", "codec"),
    (r"^Codec_\w+$", "factory", "P1", "codec"),
    (r"^Reporter_monitor$", "abstract", "P0", "reporter"),
    (r"^Reporter_(BFER|noise|throughput)$", "wrap", "P0", "reporter"),
    (r"^Reporter_\w+$", "wrap", "P2", "reporter"),
    (r"^Monitor_reduction(_static)?$", "wrap", "P2", "tools"),
    (r"^Monitor_reduction_MPI$", "skip", "-", ""),
    (r"^(Dumper|Dumper_reduction|Frame_trace)$", "wrap", "P3", "tools"),
    (r"^(Histogram)$", "wrap", "P3", "tools"),
    (r"^(Header|Command_parser)$", "func", "P1", "factory"),
]


def tool_rule(name: str):
    for pat, strat, prio, mod in TOOLS_RULES:
        if re.match(pat, name):
            return strat, prio, mod
    return "skip", "-", ""


def is_policy_template(tpl: list[str]) -> bool:
    """True if a template has non-type / policy parameters (function pointers, API_polar, Update_rule, MAX...)."""
    return any(not p.startswith("typename") for p in tpl)


def base_id(kind: str, b: str) -> tuple[str, str]:
    """Return (graph id, short name) of a base class string."""
    short = re.sub(r"<.*", "", b).strip()
    if short.startswith("spu::"):
        return "S_" + short.split("::")[-1], short.split("::")[-1]
    if short.startswith("module::"):
        return "M_" + short.split("::")[-1], short.split("::")[-1]
    if short.startswith("tools::"):
        return "T_" + short.split("::")[-1], short.split("::")[-1]
    return {"Module": "M_", "Tools": "T_", "Factory": "F_"}[kind] + short, short


def domain_of(c: dict) -> str:
    parts = Path(c["file"]).parts
    if c["kind"] == "Module":
        return parts[1]
    if c["kind"] == "Factory":
        if len(parts) < 3:
            return "Base"
        return parts[1] if parts[1] == "Tools" else parts[2]
    return parts[1] if len(parts) > 2 else "Misc"


def classify(classes: list[dict]) -> list[dict]:
    has_child = defaultdict(set)
    for c in classes:
        for b in c["bases"]:
            has_child[base_id(c["kind"], b)[0]].add(c["name"])

    seen = set()
    out = []
    for c in classes:
        pfx = {"Module": "M_", "Tools": "T_", "Factory": "F_"}[c["kind"]]
        c["id"] = pfx + c["name"]
        if c["id"] in seen or INTERNAL.match(c["name"]):
            continue
        seen.add(c["id"])
        c["domain"] = domain_of(c)
        c["bases_id"] = [base_id(c["kind"], b)[0] for b in c["bases"] if not b.startswith("std::")]
        n = c["name"]
        if c["kind"] == "Module":
            mod = PREFIX.get(c["domain"], c["domain"].lower())
            children = has_child.get(c["id"])
            if n in ABSTRACT_MODULES:
                strat, prio = "abstract", "P0"
            elif is_policy_template(c["tpl"]):
                strat, prio = "factory", "P1"
            elif children:
                strat, prio = "wrap", "P1"
            else:
                strat, prio = "wrap", "P1"
            # P0 = what is needed for the first end-to-end BFER chain (polar + LDPC + BCH/RS + AWGN/BPSK)
            p0 = re.compile(
                r"^(CRC_polynomial|CRC_NO|Channel_AWGN_LLR|Channel_NO|Encoder_(NO|polar|polar_sys|LDPC|LDPC_from_H|"
                r"repetition_sys|BCH|RS)|Decoder_(NO|repetition_std|repetition_fast|BCH_std|RS_std|polar_SC_naive|"
                r"polar_SC_naive_sys|LDPC_BP_flooding_SPA)|Modem_BPSK|Modem_BPSK_fast|Quantizer_(NO|pow2)|"
                r"Monitor_BFER|Source_random_fast|Interleaver|Puncturer_NO)$"
            )
            if prio == "P1" and P2_MODULES.search(c["file"] + "/" + n):
                prio = "P2"
            if p0.match(n) and strat != "factory":
                prio = "P0"
            if strat == "factory" and n in P0_FACTORY_ONLY:
                prio = "P0"
            short = re.sub(r"^" + c["domain"] + "_", "", n).lower()
            c["py"] = f"aff3ct.{mod}.{short}" if strat != "abstract" else f"aff3ct.{mod}.{n}"
            if strat == "factory":  # factory hidden behind the module-level function of the family
                fam = factory_for(c)
                short_fam = re.sub(r"^" + c["domain"] + "_?", "", fam).lower() or "generic"
                c["py"] = f"aff3ct.{mod}.{short_fam}(…) [factory {fam}]"
        elif c["kind"] == "Factory":
            strat = "abstract" if n == "Factory" else "wrap"
            prio = "P0" if n in P0_FACTORIES else "P1"
            c["py"] = f"(interne) aff3ct.factory.{n}"
            c["domain"] = "Factory/" + c["domain"]
        else:
            strat, prio, mod = tool_rule(n)
            c["py"] = f"aff3ct.{mod}.{n}" if strat not in ("skip",) else "—"
        c["strategy"], c["priority"] = strat, prio
        out.append(c)
    return out


# --------------------------------------------------------------------------------------------- Mermaid output

STYLE = """    classDef spu fill:#e5e7eb,stroke:#6b7280,color:#111;
    classDef abstract fill:#dbeafe,stroke:#1d4ed8,color:#111;
    classDef wrap fill:#dcfce7,stroke:#15803d,color:#111;
    classDef factory fill:#ffedd5,stroke:#c2410c,color:#111;
    classDef func fill:#f3e8ff,stroke:#7e22ce,color:#111;
    classDef skip fill:#fff,stroke:#9ca3af,color:#6b7280,stroke-dasharray: 4 3;"""


def label(c: dict) -> str:
    tpl = ",".join(re.sub(r"^(typename|class)\s+", "", p).split("=")[0].strip() for p in c["tpl"])
    tpl = f"&lt;{tpl}&gt;" if tpl else ""
    if len(tpl) > 28:
        tpl = "&lt;…&gt;"
    return f'{c["id"]}["{c["name"]}{tpl}"]:::{c["strategy"]}'


def graph(title: str, nodes: list[dict], all_by_id: dict, uses: bool = False, direction: str = "LR") -> str:
    ids = {n["id"] for n in nodes}
    lines = [f"### {title}", "", "```mermaid", f"graph {direction}", STYLE]
    extra = set()
    for n in nodes:
        lines.append("    " + label(n))
    for n in nodes:
        for b in n["bases_id"]:
            if b not in ids:
                extra.add(b)
            lines.append(f"    {b} --> {n['id']}")
        if uses:
            for u in n["uses"]:
                for pfx in ("T_", "M_"):
                    tid = pfx + u
                    if tid in all_by_id and tid != n["id"] and (pfx == "T_" or tid not in ids):
                        extra.add(tid)
                        lines.append(f"    {n['id']} -.uses.-> {tid}")
                        break
    for e in sorted(extra):
        if e.startswith("S_"):
            lines.append(f'    {e}["spu::{e[2:]}"]:::spu')
        elif e in all_by_id:
            lines.append("    " + label(all_by_id[e]))
        else:
            lines.append(f'    {e}["{e[2:]}"]:::skip')
    lines += ["```", ""]
    return "\n".join(lines)


def main() -> None:
    inc, out = Path(sys.argv[1]), Path(sys.argv[2])
    status_file = out / "status.json"
    status = json.loads(status_file.read_text()) if status_file.exists() else {}
    classes = classify(parse(inc, "Module") + parse(inc, "Tools") + parse(inc, "Factory"))
    by_id = {c["id"]: c for c in classes}
    mods = [c for c in classes if c["kind"] == "Module"]
    tools = [c for c in classes if c["kind"] == "Tools"]
    facs = [c for c in classes if c["kind"] == "Factory"]

    md = [
        "# Graphe des classes à wrapper",
        "",
        "> Fichier généré par `scripts/gen_class_graph.py` à partir des en-têtes AFF3CT — ne pas éditer à la main.",
        "",
        "Légende : gris = déjà wrappé par **pystreampu** (importé, jamais re-wrappé) · bleu = classe de base/interface "
        "(liée sans constructeur, sert au polymorphisme et au downcast) · vert = liée avec constructeur(s) · "
        "orange = atteignable **uniquement via une factory** (paramètres template de politique : `API_polar`, "
        "`Update_rule`, `MAX`, pointeurs de fonction…) · violet = fonctions libres/statiques · pointillés = non exposé.",
        "",
        "Flèche pleine = héritage C++ (à reproduire dans `py::class_<T, Bases...>`). "
        "Flèche pointillée `uses` = type demandé par un constructeur ou un `build()` : il **doit** être wrappé.",
        "",
        "## 1. Vue d'ensemble",
        "",
        "```mermaid",
        "graph LR",
        STYLE,
        '    S_Module["spu::Module"]:::spu --> S_Stateful["spu::Stateful"]:::spu',
        '    S_Itf["spu::Interface_set_seed / reset / is_done / clone / get_set_n_frames"]:::spu',
        '    S_Reporter["spu::tools::Reporter"]:::spu',
        '    S_Source["spu::Source"]:::spu',
        '    S_Stateful --> S_Source',
        '    subgraph AFF3CT_modules["aff3ct::module (Stateful)"]',
    ]
    for d in sorted(PREFIX):
        md.append(f'        M_{d}["{d}"]:::abstract')
    md += [
        "    end",
        "    S_Stateful --> AFF3CT_modules",
        "    S_Itf --> AFF3CT_modules",
        "    S_Source --> M_Source",
        '    subgraph AFF3CT_tools["aff3ct::tools"]',
        '        T_I["Interfaces frozen_bits / trellis / noise"]:::abstract',
        '        T_N["Noise, Sigma…"]:::wrap',
        '        T_C["Codes: Sparse_matrix, BCH/RS poly, Frozenbits_generator, Polar_code"]:::wrap',
        '        T_IC["Interleaver_core*"]:::wrap',
        '        T_K["Constellation*"]:::wrap',
        '        T_P["Post_processing_SISO*"]:::wrap',
        '        T_R["Reporter_BFER / EXIT / MI / noise / throughput"]:::wrap',
        '        T_CD["Codec*"]:::factory',
        "    end",
        "    S_Reporter --> T_R",
        '    F_Factory["factory::Factory"]:::abstract',
        '    F_All["factory::&lt;Module&gt; / &lt;Tool&gt; / Codec_*"]:::wrap',
        "    F_Factory --> F_All",
        "    F_All -.build.-> AFF3CT_modules",
        "    F_All -.build.-> AFF3CT_tools",
        "    AFF3CT_modules -.uses.-> AFF3CT_tools",
        "```",
        "",
        "## 2. Modules (`aff3ct::module`)",
        "",
    ]
    by_dom = defaultdict(list)
    for c in mods:
        by_dom[c["domain"]].append(c)
    for d in sorted(by_dom):
        nodes = by_dom[d]
        if d == "Decoder":
            fam = defaultdict(list)
            for n in nodes:
                sub = Path(n["file"]).parts[2] if len(Path(n["file"]).parts) > 3 else "_core"
                fam[sub].append(n)
            core = fam.pop("_core")
            md.append(graph("Decoder — hiérarchie de base (HIHO → SIHO → SISO)", core, by_id, uses=True))
            for sub in sorted(fam):
                md.append(graph(f"Decoder — {sub}", fam[sub], by_id, uses=True))
        else:
            md.append(graph(d, nodes, by_id, uses=True))

    md += ["## 3. Tools (`aff3ct::tools`) requis", ""]
    tdom = defaultdict(list)
    for c in tools:
        if c["strategy"] != "skip":
            tdom[c["domain"]].append(c)
    for d in sorted(tdom):
        md.append(graph(f"Tools / {d}", tdom[d], by_id, uses=True))

    md += ["## 4. Factories (`aff3ct::factory`)", ""]
    fdom = defaultdict(list)
    for c in facs:
        fdom[c["domain"]].append(c)
    for d in sorted(fdom):
        md.append(graph(d.replace("Factory/", "Factory — "), fdom[d], by_id, uses=True))

    skipped = sorted({c["name"] for c in tools if c["strategy"] == "skip"})
    md += [
        "## 5. Non exposé (détails d'implémentation)",
        "",
        "Ces classes ne sont jamais vues par l'utilisateur Python : elles sont choisies en interne par les factories "
        "(politiques template, SIMD, tables de constantes, structures de données internes).",
        "",
        ", ".join(f"`{s}`" for s in skipped),
        "",
    ]
    (out / "class_graph.md").write_text("\n".join(md))

    # Inventory
    rows = [
        "# Inventaire de wrapping",
        "",
        "> Généré par `scripts/gen_class_graph.py`. La colonne *Statut* vient de `status.json` "
        "(clé `Kind::Name`, valeurs `todo` → `wip` → `done`) : c'est ce fichier qu'on édite, pas celui-ci.",
        "",
    ]
    counts = defaultdict(lambda: defaultdict(int))
    for c in classes:
        counts[c["kind"]][c["strategy"]] += 1
    rows += ["| Espace | " + " | ".join(["abstract", "wrap", "factory", "func", "skip"]) + " |", "|---|---|---|---|---|---|"]
    for k in ("Module", "Tools", "Factory"):
        rows.append(f"| {k} | " + " | ".join(str(counts[k][s]) for s in ["abstract", "wrap", "factory", "func", "skip"]) + " |")
    rows.append("")
    for k, lst in (("Modules", mods), ("Tools", [t for t in tools if t["strategy"] != "skip"]), ("Factories", facs)):
        rows += [f"## {k}", "", "| Classe | En-tête | Template | Bases | Stratégie | Priorité | Nom Python | Statut |",
                 "|---|---|---|---|---|---|---|---|"]
        for c in sorted(lst, key=lambda x: (x["priority"], x["file"], x["name"])):
            tpl = ", ".join(c["tpl"]).replace("|", "\\|")
            if len(tpl) > 50:
                tpl = tpl[:47] + "…"
            bases = ", ".join(re.sub(r"<.*", "", b) for b in c["bases"])
            rows.append(
                f"| `{c['name']}` | `{c['file']}` | `{tpl}` | {bases} | {c['strategy']} | {c['priority']} | "
                f"`{c['py']}` | {status.get(c['kind'] + '::' + c['name'], 'todo')} |"
            )
        rows.append("")
    (out / "inventory.md").write_text("\n".join(rows))
    keep = ("kind", "name", "file", "tpl", "bases", "uses", "domain", "strategy", "priority", "py")
    (out / "inventory.json").write_text(json.dumps([{k: c[k] for k in keep} for c in classes], indent=1))
    print({k: dict(v) for k, v in counts.items()})


if __name__ == "__main__":
    main()
