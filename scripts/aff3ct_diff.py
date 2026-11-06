#!/usr/bin/env python3
"""Compare two AFF3CT API fingerprints (see aff3ct_api.py) and report what matters for pyaff3ct.

Usage:
    python3 scripts/aff3ct_diff.py old.json new.json [--status docs/design/status.json]
                                   [-o report.md] [--fail-on-impact]

Every change is classified by its effect on the bindings:

* BREAKING : the binding code or the Python API must change (class / constructor / method /
             task / socket / factory parameter / instantiation removed or changed, base class changed);
* DEFAULTS : a default value changed (the Python API mirrors the C++ defaults);
* ADDED    : something new to wrap (new class, constructor, method, task, parameter, instantiation).

Changes are crossed with ``status.json`` (``{"Module::Encoder_polar": "done", ...}``): a BREAKING or DEFAULTS
change on a ``done``/``wip`` class is an *action*; on a ``todo`` class it is information for the backlog.
With ``--fail-on-impact`` the exit code is 1 when at least one action exists (for CI).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ACTIVE = {"done", "wip"}


def strip_default(param: str) -> str:
    return re.split(r"\s=\s", param, maxsplit=1)[0].strip()


def member_key(m: str) -> tuple[str, str]:
    """'int L = 8' -> ('L', 'int L = 8')."""
    left = strip_default(m)
    name = re.findall(r"(\w+)\s*(?:\[.*\])?$", left)
    return (name[0] if name else left), m


def method_name(sig: str) -> str:
    sig = re.sub(r"^template<.*?>(?=[\w~:])", "", sig)
    m = re.search(r"(operator\S*|~?\w+)\s*\(", sig)
    return m.group(1) if m else sig


class Report:
    def __init__(self, status: dict[str, str]):
        self.status = status
        self.items: dict[str, list] = defaultdict(list)  # level -> [(cls, text)]

    def add(self, level: str, cls: str, text: str) -> None:
        self.items[level].append((cls, text))

    def is_action(self, level: str, cls: str) -> bool:
        return level in ("BREAKING", "DEFAULTS") and self.status.get(cls, "todo") in ACTIVE

    def n_actions(self) -> int:
        return sum(self.is_action(lvl, c) for lvl, lst in self.items.items() for c, _ in lst)


def diff_lists(rep: Report, cls: str, what: str, old: list, new: list) -> None:
    o, n = set(map(str, old)), set(map(str, new))
    for x in sorted(o - n):
        rep.add("BREAKING", cls, f"{what} supprimé(e) : `{x}`")
    for x in sorted(n - o):
        rep.add("ADDED", cls, f"{what} ajouté(e) : `{x}`")


def diff_ctors(rep: Report, cls: str, old: list, new: list) -> None:
    o = {tuple(map(strip_default, c)): c for c in old}
    n = {tuple(map(strip_default, c)): c for c in new}
    for k in sorted(set(o) - set(n)):
        rep.add("BREAKING", cls, f"constructeur supprimé ou modifié : `({', '.join(o[k])})`")
    for k in sorted(set(n) - set(o)):
        rep.add("ADDED", cls, f"constructeur ajouté : `({', '.join(n[k])})`")
    for k in sorted(set(o) & set(n)):
        if o[k] != n[k]:
            rep.add("DEFAULTS", cls, f"valeurs par défaut du constructeur : `({', '.join(o[k])})` → `({', '.join(n[k])})`")


def inherited_methods(classes: dict, cls: str, seen: set | None = None) -> dict[str, str]:
    """Method names reachable through the base classes of `cls` -> class that defines them."""
    seen = seen or set()
    kind = cls.split("::")[0]
    res: dict[str, str] = {}
    for b in classes.get(cls, {}).get("bases", []):
        short = re.sub(r"<.*", "", b).split("::")[-1]
        for k in (f"{kind}::{short}", f"Module::{short}", f"Tools::{short}"):
            if k in classes and k not in seen:
                seen.add(k)
                for m in classes[k].get("methods", []):
                    res.setdefault(method_name(m), short)
                for n, where in inherited_methods(classes, k, seen).items():
                    res.setdefault(n, where)
                break
    return res


def diff_methods(rep: Report, cls: str, old: list, new: list, inherited: dict[str, str] | None = None) -> None:
    inherited = inherited or {}
    o, n = defaultdict(set), defaultdict(set)
    for s in old:
        o[method_name(s)].add(s)
    for s in new:
        n[method_name(s)].add(s)
    for name in sorted(set(o) | set(n)):
        if o[name] == n[name]:
            continue
        if not n[name] and name in inherited:
            rep.add("INFO", cls, f"méthode `{name}` désormais héritée de `{inherited[name]}`")
        elif not n[name]:
            rep.add("BREAKING", cls, f"méthode supprimée : `{name}` ({'; '.join(sorted(o[name]))})")
        elif not o[name]:
            rep.add("ADDED", cls, f"méthode ajoutée : `{'; '.join(sorted(n[name]))}`")
        else:
            olds, news = sorted(o[name] - n[name]), sorted(n[name] - o[name])
            lvl = "DEFAULTS" if {strip_default(x) for x in olds} == {strip_default(x) for x in news} else "BREAKING"
            rep.add(lvl, cls, f"signature de `{name}` : `{'; '.join(olds)}` → `{'; '.join(news)}`")


def diff_members(rep: Report, cls: str, old: list, new: list) -> None:
    o, n = dict(map(member_key, old)), dict(map(member_key, new))
    for k in sorted(set(o) - set(n)):
        rep.add("BREAKING", cls, f"paramètre/attribut supprimé : `{o[k]}`")
    for k in sorted(set(n) - set(o)):
        rep.add("ADDED", cls, f"paramètre/attribut ajouté : `{n[k]}`")
    for k in sorted(set(o) & set(n)):
        if o[k] != n[k]:
            lvl = "DEFAULTS" if strip_default(o[k]) == strip_default(n[k]) else "BREAKING"
            rep.add(lvl, cls, f"paramètre/attribut `{k}` : `{o[k]}` → `{n[k]}`")


def diff_tasks(rep: Report, cls: str, old: dict, new: dict) -> None:
    for t in sorted(set(old) - set(new)):
        rep.add("BREAKING", cls, f"tâche supprimée : `{t}`")
    for t in sorted(set(new) - set(old)):
        socks = ", ".join(f"{d}:{n}<{ty}>" for d, ty, n in new[t])
        rep.add("ADDED", cls, f"tâche ajoutée : `{t}({socks})`")
    for t in sorted(set(old) & set(new)):
        o = {s[2]: s for s in old[t]}
        n = {s[2]: s for s in new[t]}
        for s in sorted(set(o) - set(n)):
            rep.add("BREAKING", cls, f"socket supprimée : `{t}::{s}`")
        for s in sorted(set(n) - set(o)):
            rep.add("ADDED", cls, f"socket ajoutée : `{t}::{s}` ({n[s][0]}, {n[s][1]})")
        for s in sorted(set(o) & set(n)):
            if o[s] != n[s]:
                rep.add("BREAKING", cls, f"socket `{t}::{s}` : {o[s][0]}<{o[s][1]}> → {n[s][0]}<{n[s][1]}>")
        if [x[2] for x in old[t] if x[2] in n] != [x[2] for x in new[t] if x[2] in o]:
            rep.add("BREAKING", cls, f"ordre des sockets de `{t}` modifié (appel positionnel Python)")


def compare(old: dict, new: dict, status: dict) -> Report:
    rep = Report(status)
    oc, nc = old["classes"], new["classes"]
    for cls in sorted(set(oc) - set(nc)):
        rep.add("BREAKING", cls, f"classe supprimée (`{oc[cls]['file']}`)")
    for cls in sorted(set(nc) - set(oc)):
        e = nc[cls]
        tpl = f"<{', '.join(e['tpl'])}>" if e["tpl"] else ""
        rep.add("ADDED", cls, f"nouvelle classe `{e['file']}` {tpl} : {', '.join(e['bases']) or '—'}")
    for cls in sorted(set(oc) & set(nc)):
        o, n = oc[cls], nc[cls]
        if o["file"] != n["file"]:
            rep.add("BREAKING", cls, f"en-tête déplacé : `{o['file']}` → `{n['file']}`")
        if o["tpl"] != n["tpl"]:
            lvl = "DEFAULTS" if list(map(strip_default, o["tpl"])) == list(map(strip_default, n["tpl"])) else "BREAKING"
            rep.add(lvl, cls, f"paramètres template : `{o['tpl']}` → `{n['tpl']}`")
        if o["bases"] != n["bases"]:
            rep.add("BREAKING", cls, f"classes de base : `{o['bases']}` → `{n['bases']}`")
        diff_ctors(rep, cls, o.get("ctors", []), n.get("ctors", []))
        diff_methods(rep, cls, o.get("methods", []), n.get("methods", []), inherited_methods(nc, cls))
        diff_members(rep, cls, o.get("members", []), n.get("members", []))
        diff_tasks(rep, cls, o.get("tasks") or {}, n.get("tasks") or {})
        diff_lists(rep, cls, "instanciation", o.get("instantiations", []), n.get("instantiations", []))
    return rep


LEVELS = [
    ("BREAKING", "Changements cassants", "le binding ou l'API Python doit changer"),
    ("DEFAULTS", "Valeurs par défaut modifiées", "l'API Python reprend les défauts C++"),
    ("ADDED", "Ajouts", "à classer et wrapper (relancer `gen_class_graph.py`)"),
    ("INFO", "Réorganisations sans impact attendu", "vérification rapide"),
]


def render(old: dict, new: dict, rep: Report, info: dict[str, str] | None = None) -> str:
    info = info or {}
    om, nm = old["meta"], new["meta"]
    out = [
        f"# Évolution d'AFF3CT : {om.get('describe')} → {nm.get('describe')}",
        "",
        f"- Ancien : `{om.get('commit', '')[:10]}` ({om.get('date')})",
        f"- Nouveau : `{nm.get('commit', '')[:10]}` ({nm.get('date')})",
    ]
    for sub, label in (("streampu", "StreamPU"), ("cli", "cli")):
        if om.get(sub) != nm.get(sub):
            warn = " — **vérifier que pystreampu épingle le même commit**" if sub == "streampu" else ""
            out.append(f"- **{label} modifié** : `{om.get(sub, '')[:10]}` → `{nm.get(sub, '')[:10]}`{warn}")
        else:
            out.append(f"- {label} inchangé : `{nm.get(sub, '')[:10]}`")
    out += ["", "| Niveau | Total | Sur classes `done`/`wip` (actions) |", "|---|---|---|"]
    for lvl, title, _ in LEVELS:
        lst = rep.items.get(lvl, [])
        act = sum(rep.is_action(lvl, c) for c, _ in lst)
        out.append(f"| {title} | {len(lst)} | {act if lvl in ('BREAKING', 'DEFAULTS') else '—'} |")
    out.append("")
    if rep.n_actions():
        out += ["## ⚠️ Actions requises (classes déjà wrappées)", ""]
        for lvl, title, _ in LEVELS[:2]:
            for c, t in rep.items.get(lvl, []):
                if rep.is_action(lvl, c):
                    out.append(f"- **{c}** [{rep.status[c]}] — {t}")
        out.append("")
    for lvl, title, hint in LEVELS:
        lst = rep.items.get(lvl, [])
        if not lst:
            continue
        out += [f"## {title} ({len(lst)}) — {hint}", ""]
        by_cls = defaultdict(list)
        for c, t in lst:
            by_cls[c].append(t)
        for c in sorted(by_cls):
            st = rep.status.get(c, "todo")
            how = f" — {info[c]}" if c in info else ""
            out.append(f"<details><summary><code>{c}</code> [{st}{how}] — {len(by_cls[c])} changement(s)</summary>\n")
            out += [f"- {t}" for t in by_cls[c]]
            out.append("\n</details>")
        out.append("")
    if not any(rep.items.values()):
        out.append("Aucun changement d'API détecté.")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("old", type=Path)
    ap.add_argument("new", type=Path)
    ap.add_argument("--status", type=Path, default=Path(__file__).parent.parent / "docs/design/status.json")
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--fail-on-impact", action="store_true")
    a = ap.parse_args()
    old, new = json.loads(a.old.read_text()), json.loads(a.new.read_text())
    status = json.loads(a.status.read_text()) if a.status.exists() else {}
    rep = compare(old, new, status)
    md = render(old, new, rep)
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(md)
    else:
        sys.stdout.write(md)
    counts = {lvl: len(rep.items.get(lvl, [])) for lvl, _, _ in LEVELS}
    print(f"{counts} ; actions sur classes wrappées : {rep.n_actions()}", file=sys.stderr)
    return 1 if a.fail_on_impact and rep.n_actions() else 0


if __name__ == "__main__":
    sys.exit(main())
