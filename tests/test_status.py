"""docs/design/status.json tells the AFF3CT tracking (scripts/track_aff3ct.py) which classes are wrapped: it must be
true, otherwise an upstream breaking change on a wrapped class would not be reported as an action."""

import json
import re
from pathlib import Path

import aff3ct as af

DESIGN = Path(__file__).parent.parent / "docs" / "design"
STATUS = json.loads((DESIGN / "status.json").read_text())
API = json.loads((DESIGN / "aff3ct_api.json").read_text())["classes"]
SUFFIX = re.compile(r"_(u?int(8|16|32|64)|float(32|64))(_(u?int(8|16|32|64)|float(32|64)))*$")


def _registered():
    names = set()
    for sub in vars(af._ext).values():
        if hasattr(sub, "__dict__") and getattr(sub, "__name__", "").startswith("aff3ct._ext"):
            for n, obj in vars(sub).items():
                if isinstance(obj, type):
                    names.add((sub.__name__.split(".")[-1], SUFFIX.sub("", n)))
    return names


def test_status_keys_exist_in_the_aff3ct_api():
    assert set(STATUS) <= set(API), sorted(set(STATUS) - set(API))
    assert set(STATUS.values()) <= {"todo", "wip", "done"}


def test_done_classes_are_registered():
    registered = _registered()
    for key, st in STATUS.items():
        if st != "done":
            continue
        kind, name = key.split("::")
        where = {s for s, n in registered if n == name}
        if kind == "Factory":
            assert "factory" in where, key
        else:
            assert where - {"factory"}, f"{key} is marked done but not registered in aff3ct._ext"
