#!/usr/bin/env python3
"""Extract the API fingerprint of an AFF3CT source tree.

Usage:
    python3 scripts/aff3ct_api.py <path/to/aff3ct> -o docs/design/aff3ct_api.json

The fingerprint contains everything the Python bindings depend on, class by class
(``<Kind>::<Name>`` with Kind in Module / Tools / Factory):

* ``file``, ``tpl`` (template parameters) and ``bases``;
* ``ctors``: public constructor parameter lists (types *and* default values);
* ``methods``: public method signatures;
* ``members``: public data members (factory parameters, with their default value);
* ``tasks``: ``{task: [[direction, dtype, socket], ...]}`` created by the class;
* ``instantiations``: explicit template instantiations of the multi-precision build
  (classes and factory ``build*`` methods), i.e. the dtype combinations Python can use.

plus a ``meta`` section (AFF3CT commit, version, StreamPU / cli submodule commits).

``scripts/aff3ct_diff.py`` compares two fingerprints.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

CLS_RE = re.compile(
    r"(template\s*<(?P<tpl>[^{;]*?)>\s*)?"
    r"(?<!enum )(class|struct)\s+(?P<name>[A-Za-z_]\w*)\s*(final\s*)?"
    r"(:\s*(?P<bases>[^{;]*))?\{",
    re.S,
)
MSVC_RE = re.compile(r"#ifdef _MSC_VER\s*\n.*?#else\s*\n(.*?)#endif", re.S)
TASK_RE = re.compile(r"(?:auto\s*&\s*)?(\w+)\s*=\s*this->create_task\s*\(\s*\"(\w+)\"")
SOCKET_RE = re.compile(
    r"create_socket_(in|out|fwd)\s*(?:<\s*([^>]+?)\s*>)?\s*\(\s*(\w+)\s*,\s*\"(\w+)\"",
)
INST_CLASS_RE = re.compile(r"template\s+class\s+aff3ct::\w+::(\w+)\s*<(.*?)>\s*;", re.S)
INST_BUILD_RE = re.compile(r"aff3ct::factory::(\w+)::(build\w*)\s*<(.*?)>\s*\(", re.S)
KIND_PFX = {"Module": "Module", "Tools": "Tools", "Factory": "Factory"}


def ws(s: str) -> str:
    """Normalize a C++ declaration so that formatting-only changes do not show up in diffs."""
    s = " ".join(s.split())
    s = re.sub(r"\s*([<>(),=])\s*", r"\1", s)
    s = re.sub(r"\s*([&*]+)\s*", r"\1 ", s)
    s = re.sub(r"([&*]) ([>),])", r"\1\2", s)
    s = s.replace(",", ", ").replace("=", " = ").replace("operator = ", "operator=").replace("+ = ", "+= ")
    return re.sub(r"= =", "==", s).strip()


def strip(txt: str) -> str:
    txt = re.sub(r"//[^\n]*", "", txt)
    txt = re.sub(r"/\*.*?\*/", "", txt, flags=re.S)
    return MSVC_RE.sub(r"\1", txt)


def split_top(s: str, sep: str = ",") -> list[str]:
    out, depth, cur = [], 0, ""
    for ch in s:
        depth += ch in "<({["
        depth -= ch in ">)}]"
        if ch == sep and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return [ws(x) for x in out if x.strip()]


def class_body(txt: str, start: int) -> str:
    depth, i = 1, start
    while i < len(txt) and depth:
        depth += txt[i] == "{"
        depth -= txt[i] == "}"
        i += 1
    return txt[start : i - 1]


def statements(body: str):
    """Yield (access, statement) for the top-level statements of a class body."""
    cur, depth, quote = "", 0, None
    for ch in body:
        if quote:  # inside a string / char literal: braces and ';' are plain characters
            if depth == 0:
                cur += ch
            if ch == quote and not cur.endswith("\\" + quote):
                quote = None
            continue
        if ch in "\"'":
            quote = ch
            if depth == 0:
                cur += ch
            continue
        if depth == 0 and ch == ";":
            yield cur
            cur = ""
            continue
        if ch == "{":
            depth += 1
            if depth == 1:
                cur += "{}"
            continue
        if ch == "}":
            depth -= 1
            if depth == 0 and not re.search(r"=\s*\{\}$", cur.strip()):
                yield cur
                cur = ""
            continue
        if depth == 0:
            cur += ch
    if cur.strip():
        yield cur


def parse_members(name: str, body: str, is_struct: bool) -> dict:
    access = "public" if is_struct else "private"
    res = {"ctors": [], "methods": [], "members": []}
    for st in statements(body):
        # access labels may be glued in front of the statement
        while True:
            m = re.match(r"\s*(public|protected|private)\s*:(?!:)", st)
            if not m:
                break
            access = m.group(1)
            st = st[m.end() :]
        st = st.strip()
        if not st or access != "public" or st.startswith(("using ", "friend ", "typedef ", "static_assert")):
            continue
        st = re.sub(r"\{\}$", "", st).strip()
        st_n = ws(re.sub(r"^(inline|virtual|explicit|static|constexpr)\s+", "", st))
        decl = re.sub(r"^template\s*<.*?>\s*(?=[\w~:])", "", st_n)  # drop a leading template<...>
        decl = re.sub(r"^(inline|virtual|explicit|static|constexpr)\s+", "", decl)
        if re.match(r"(~)?" + name + r"\s*\(", st_n) or re.match(r"template<[^>]*>\s*" + name + r"\(", st_n):
            if st_n.startswith("~"):
                continue
            params = re.search(r"\((.*)\)", st_n, re.S)
            res["ctors"].append(split_top(params.group(1)) if params else [])
        elif "(" in decl and ("operator" in decl.split("(")[0] or not re.match(r"^[^(]*=", decl)):
            res["methods"].append(re.sub(r"\s*(override|final)\b", "", st_n))
        else:
            res["members"].append(st_n)
    for k in res:
        res[k] = sorted(set(map(json.dumps, res[k])))
        res[k] = [json.loads(x) for x in res[k]]
    return res


def parse_tasks(texts: list[str]) -> dict:
    tasks: dict[str, list] = {}
    for txt in texts:
        var2task = {}
        for m in TASK_RE.finditer(txt):
            var2task[m.group(1)] = m.group(2)
            tasks.setdefault(m.group(2), [])
        for m in SOCKET_RE.finditer(txt):
            task = var2task.get(m.group(3))
            if task is None:
                continue
            entry = [m.group(1), ws(m.group(2) or "?"), m.group(4)]
            if entry not in tasks[task]:
                tasks[task].append(entry)
    return tasks


def parse_instantiations(txt: str) -> dict[str, list[str]]:
    # multi-precision block when there is one, otherwise unconditional instantiations (e.g. Noise<float/double>)
    blocks = re.findall(r"#ifdef\s+AFF3CT_MULTI_PREC(.*?)#(?:else|endif)", txt, re.S)
    block = "\n".join(blocks) if blocks else txt
    res: dict[str, set] = {}
    for c in INST_CLASS_RE.finditer(block):
        res.setdefault(c.group(1), set()).add(ws(c.group(2)))
    for b in INST_BUILD_RE.finditer(block):
        res.setdefault(b.group(1), set()).add(f"{b.group(2)}<{ws(b.group(3))}>")
    return {k: sorted(v) for k, v in res.items()}


def git(root: Path, *args: str) -> str:
    try:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def submodule_sha(root: Path, path: str) -> str:
    out = git(root, "ls-tree", "HEAD", path)
    return out.split()[2] if out else ""


def fingerprint(root: Path) -> dict:
    inc, src = root / "include", root / "src"
    # index implementation files by stem (tasks/sockets & instantiations live there)
    impl: dict[str, list[Path]] = {}
    for f in list(src.rglob("*.cpp")) + list(inc.rglob("*.hxx")):
        impl.setdefault(f.stem, []).append(f)
    inst: dict[str, dict] = {}
    for f in src.rglob("*.cpp"):
        kind = f.relative_to(src).parts[0]
        for name, combos in parse_instantiations(f.read_text(errors="ignore")).items():
            inst.setdefault(f"{kind}::{name}", {}).setdefault("_", []).extend(combos)

    classes = {}
    for kind in ("Module", "Tools", "Factory"):
        for f in sorted((inc / kind).rglob("*.hpp")):
            txt = strip(f.read_text(errors="ignore"))
            for m in CLS_RE.finditer(txt):
                name = m.group("name")
                key = f"{kind}::{name}"
                if key in classes:
                    continue
                body = class_body(txt, m.end())
                entry = {
                    "file": str(f.relative_to(inc)),
                    "tpl": split_top(m.group("tpl") or ""),
                    "bases": [re.sub(r"^(public|protected|private|virtual)\s+", "", b)
                              for b in split_top(m.group("bases") or "")],
                }
                entry.update(parse_members(name, body, m.group(3) == "struct"))
                if kind == "Module":
                    texts = [strip(p.read_text(errors="ignore")) for p in impl.get(name, [])]
                    entry["tasks"] = parse_tasks(texts)
                entry["instantiations"] = sorted(set(inst.get(key, {}).get("_", [])))
                classes[key] = entry

    meta = {
        "commit": git(root, "rev-parse", "HEAD"),
        "describe": git(root, "describe", "--tags", "--always"),
        # exact tag of the commit, if any: unlike `describe`, it does not depend on the depth of the clone
        "tag": git(root, "describe", "--tags", "--exact-match"),
        "date": git(root, "log", "-1", "--format=%cs"),
        "streampu": submodule_sha(root, "lib/streampu"),
        "cli": submodule_sha(root, "lib/cli"),
    }
    return {"meta": meta, "classes": classes}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("aff3ct", type=Path, help="AFF3CT source tree (contains include/ and src/)")
    ap.add_argument("-o", "--output", type=Path, required=True)
    a = ap.parse_args()
    fp = fingerprint(a.aff3ct)
    a.output.write_text(json.dumps(fp, indent=1, sort_keys=True) + "\n")
    print(f"{len(fp['classes'])} classes, AFF3CT {fp['meta']['describe']} ({fp['meta']['commit'][:8]})")


if __name__ == "__main__":
    main()
