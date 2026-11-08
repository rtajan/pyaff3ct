"""Reading the AFF3CT reference curves (lib/aff3ct/refs, the ``refs`` submodule of AFF3CT) for the examples."""

from __future__ import annotations

import re
from pathlib import Path

REFS = Path(__file__).resolve().parent.parent / "lib" / "aff3ct" / "refs"


def available() -> bool:
    return REFS.is_dir() and any(REFS.iterdir())


def read(name: str) -> dict[str, list[float]]:
    """Columns of a reference with an Eb/N0 noise: {"ebn0": [...], "fra": [...], "ber": [...], "fer": [...]}."""
    out: dict[str, list[float]] = {"ebn0": [], "fra": [], "ber": [], "fer": []}
    for line in (REFS / name).read_text().splitlines():
        cols = [c.strip() for c in re.split(r"\|\|?", line)]
        if len(cols) >= 7 and re.fullmatch(r"-?[0-9.]+", cols[1] or "x") and re.fullmatch(r"[0-9]+", cols[2] or "x"):
            out["ebn0"].append(float(cols[1]))
            out["fra"].append(int(cols[2]))
            out["ber"].append(float(cols[5]))
            out["fer"].append(float(cols[6]))
    return out


def command(name: str) -> str:
    """AFF3CT command line of a reference."""
    return next(line for line in (REFS / name).read_text().splitlines() if line.startswith("command="))[8:]
