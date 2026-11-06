#!/usr/bin/env python3
"""Track the evolution of AFF3CT for pyaff3ct.

Compares the AFF3CT API between a baseline and a target revision and writes a report in
``docs/design/changes/``. The working tree of the AFF3CT repository is never modified:
each revision is checked out in a temporary ``git worktree``.

Examples:
    # What changed upstream since the revision pyaff3ct is aligned on (docs/design/aff3ct_api.json)?
    python3 scripts/track_aff3ct.py --repo lib/aff3ct --fetch --to origin/develop

    # Compare two explicit revisions (e.g. the one used by _pyaff3ct and the current one)
    python3 scripts/track_aff3ct.py --repo lib/aff3ct --from v4.1.2 --to HEAD

    # Accept the target: refresh the baseline fingerprint, the class graph and the inventory
    python3 scripts/track_aff3ct.py --repo lib/aff3ct --to HEAD --update

Exit code: 1 with ``--fail-on-impact`` when a change hits a class marked done/wip in status.json.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DESIGN = ROOT / "docs" / "design"
sys.path.insert(0, str(HERE))

import aff3ct_api  # noqa: E402
import aff3ct_diff  # noqa: E402
import gen_class_graph  # noqa: E402

KIND = {"M_": "Module", "T_": "Tools", "F_": "Factory"}


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


@contextmanager
def checkout(repo: Path, ref: str):
    """Yield a temporary worktree of `repo` at `ref` (removed afterwards)."""
    with tempfile.TemporaryDirectory(prefix="aff3ct-") as tmp:
        wt = Path(tmp) / "wt"
        git(repo, "worktree", "add", "--detach", "--quiet", str(wt), ref)
        try:
            yield wt
        finally:
            git(repo, "worktree", "remove", "--force", str(wt))


def fingerprint_at(repo: Path, ref: str) -> tuple[dict, dict[str, str]]:
    """API fingerprint of `ref` and wrapping classification of its classes ("Kind::Name" -> "strategy Px")."""
    with checkout(repo, ref) as wt:
        inc = wt / "include"
        parsed = sum((gen_class_graph.parse(inc, k) for k in ("Module", "Tools", "Factory")), [])
        info = {f"{KIND[c['id'][:2]]}::{c['name']}": f"{c['strategy']} {c['priority']}"
                for c in gen_class_graph.classify(parsed)}
        return aff3ct_api.fingerprint(wt), info


def revision_name(meta: dict) -> str:
    """Stable name of a revision: its exact tag (v4.7.2), otherwise its short commit hash."""
    return meta.get("tag") or meta["commit"][:8]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", type=Path, required=True, help="AFF3CT git repository (e.g. lib/aff3ct)")
    ap.add_argument("--from", dest="from_ref", help="baseline revision (default: docs/design/aff3ct_api.json)")
    ap.add_argument("--to", dest="to_ref", default="HEAD", help="target revision (default: HEAD)")
    ap.add_argument("--fetch", action="store_true", help="git fetch the repository first")
    ap.add_argument("--update", action="store_true",
                    help="store the target as the new baseline and regenerate class_graph.md / inventory.*")
    ap.add_argument("--fail-on-impact", action="store_true")
    a = ap.parse_args()

    if a.fetch:
        git(a.repo, "fetch", "--quiet", "--tags", "origin")
    baseline_file = DESIGN / "aff3ct_api.json"
    if a.from_ref:
        old, _ = fingerprint_at(a.repo, a.from_ref)
    elif baseline_file.exists():
        old = json.loads(baseline_file.read_text())
    else:
        sys.exit("no baseline: pass --from <ref> or run once with --update")
    new, info = fingerprint_at(a.repo, a.to_ref)

    status_file = DESIGN / "status.json"
    status = json.loads(status_file.read_text()) if status_file.exists() else {}
    rep = aff3ct_diff.compare(old, new, status)
    name = f"{revision_name(old['meta'])}..{revision_name(new['meta'])}"
    out = DESIGN / "changes" / f"{name}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(aff3ct_diff.render(old, new, rep, info))
    counts = {lvl: len(rep.items.get(lvl, [])) for lvl, _, _ in aff3ct_diff.LEVELS}
    print(f"report: {out.relative_to(ROOT)}  {counts}  actions: {rep.n_actions()}")

    if a.update:
        baseline_file.write_text(json.dumps(new, indent=1, sort_keys=True) + "\n")
        with checkout(a.repo, a.to_ref) as wt:
            subprocess.run([sys.executable, str(HERE / "gen_class_graph.py"), str(wt / "include"), str(DESIGN)],
                           check=True)
        print(f"baseline updated to {new['meta']['describe']} ({new['meta']['commit'][:8]})")
    return 1 if a.fail_on_impact and rep.n_actions() else 0


if __name__ == "__main__":
    sys.exit(main())
