#!/usr/bin/env python3
"""Type stubs (.pyi) of the aff3ct package, for the autocompletion and the type checkers of the IDEs.

Called by CMake after the build of the extension (option PYAFF3CT_STUBS); the stubs are installed with the package
(next to its modules, ``aff3ct/_ext/*.pyi`` next to the extension), never written in the source tree: a directory
``aff3ct/_ext/`` in the sources would shadow the extension when Python is started from the root of the repository.

    python scripts/gen_stubs.py --ext build/dev/_ext.cpython-313-x86_64-linux-gnu.so --out build/dev/stubs

The package is imported from a staging copy (its .py files and the given extension), with pybind11-stubgen.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "aff3ct"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ext", required=True, type=Path, help="built extension (_ext*.so / _ext*.pyd)")
    p.add_argument("--out", required=True, type=Path, help="output directory (receives aff3ct/**/*.pyi)")
    p.add_argument("--src", type=Path, default=SRC, help="Python sources of the package")
    a = p.parse_args()

    with tempfile.TemporaryDirectory(prefix="aff3ct-stubs-") as tmp:
        stage = Path(tmp) / "aff3ct"
        for f in a.src.rglob("*.py"):  # the Python modules only: no stale .pyi or _ext/ directory
            if "__pycache__" not in f.parts:
                dst = stage / f.relative_to(a.src)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dst)
        if not (stage / "_version.py").exists():  # written by setuptools_scm at the build of the wheel
            (stage / "_version.py").write_text('version = __version__ = "0.0.0"\n')
        shutil.copy2(a.ext, stage / a.ext.name)

        out = Path(tmp) / "stubs"
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([tmp, os.environ.get("PYTHONPATH", "")]).rstrip(os.pathsep)}
        cmd = [sys.executable, "-m", "pybind11_stubgen", "aff3ct", "-o", str(out), "--exit-code"]
        r = subprocess.run(cmd, cwd=tmp, env=env)  # cwd: not the root of the repository (its aff3ct/ would win)
        if r.returncode:
            print("gen_stubs: pybind11-stubgen failed (see above)", file=sys.stderr)
            return r.returncode
        for stub in out.rglob("*.pyi"):
            # re-exports of the sub-modules (from aff3ct._ext.dec import Decoder...): listed in __all__, which some
            # completion engines (jedi) read only when it is not annotated (pybind11-stubgen: "__all__: list = [...]")
            text = stub.read_text()
            new = re.sub(r"^__all__: list(\[str\])? = ", "__all__ = ", text, count=1, flags=re.M)
            if new != text:
                stub.write_text(new)
        (out / "aff3ct" / "py.typed").write_text("")  # PEP 561: the package is typed
        shutil.rmtree(a.out, ignore_errors=True)
        shutil.copytree(out, a.out)
    n = sum(1 for _ in a.out.rglob("*.pyi"))
    print(f"gen_stubs: {n} stubs -> {a.out / 'aff3ct'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
