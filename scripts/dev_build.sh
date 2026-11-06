#!/usr/bin/env bash
# Development build of pyaff3ct: configure + build in build/dev, then link the extension into the source tree so
# that `import aff3ct` and `pytest` work without installing the package.
#
#   scripts/dev_build.sh                  # uses `python3` (the environment where streampu is installed)
#   PYTHON=path/to/python scripts/dev_build.sh
#   JOBS=8 ARCH_FLAGS=-march=native scripts/dev_build.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
BUILD="${BUILD:-$ROOT/build/dev}"
JOBS="${JOBS:-$(nproc 2>/dev/null || sysctl -n hw.ncpu)}"

"$PYTHON" -c "import streampu" || { echo "streampu (pystreampu) must be installed for $PYTHON" >&2; exit 1; }

cmake_args=(-S "$ROOT" -B "$BUILD" -DCMAKE_BUILD_TYPE=Release -DPython_EXECUTABLE="$(command -v "$PYTHON")"
            "-DCMAKE_CXX_FLAGS=-Wall -funroll-loops -fvisibility=hidden -fvisibility-inlines-hidden")
command -v ninja > /dev/null && cmake_args+=(-G Ninja)
[ -n "${ARCH_FLAGS:-}" ] && cmake_args+=("-DPYAFF3CT_ARCH_FLAGS=$ARCH_FLAGS")
[ -f "$BUILD/CMakeCache.txt" ] || cmake "${cmake_args[@]}"

cmake --build "$BUILD" --target _ext -j "$JOBS"

ext="$(find "$BUILD" -maxdepth 1 \( -name "_ext*.so" -o -name "_ext*.pyd" \) | head -1)"
[ -n "$ext" ] || { echo "the extension was not built in $BUILD" >&2; exit 1; }
ln -sf "$ext" "$ROOT/aff3ct/$(basename "$ext")"
echo "aff3ct/$(basename "$ext") -> $ext"
