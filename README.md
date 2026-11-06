# pyaff3ct

Python bindings (pybind11) for [AFF3CT](https://github.com/aff3ct/aff3ct), built on top of
[pystreampu](https://github.com/aff3ct/pystreampu): every AFF3CT module is a `streampu.Module`,
its tasks are callable from Python and its sockets are exposed as NumPy arrays.

Status: phase 1 (infrastructure: dtype dispatch, abstract module bases, factories, conversions) — see `Plan.md`.

## Development build

Requires an environment where `streampu` (pystreampu) is installed: pyaff3ct is built against its pybind11 and
StreamPU versions.

```bash
git submodule update --init lib/aff3ct
git -C lib/aff3ct submodule update --init --recursive lib/cli lib/MIPP lib/date
PYTHON=path/to/python scripts/dev_build.sh       # build/dev, links aff3ct/_ext*.so into the source tree
path/to/python -m pytest
```

The first build compiles AFF3CT in multi-precision (about 15 minutes on 2 cores). `ARCH_FLAGS=-march=native`
tunes it for the host (default on x86-64: `-msse4.2`).

```python
import streampu as spu
import aff3ct as af

crc = af.factory.CRC.from_cli("--crc-type 32-GZIP", K=64).build(B=spu.int16)
x = crc.build(spu.array([0, 1] * 32, dtype=spu.int16))   # AFF3CT task executed by pystreampu
```

## Design documents

- [`Plan.md`](Plan.md) — architecture, wrapping rules and roadmap;
- [`docs/design/class_graph.md`](docs/design/class_graph.md) — graph of the classes to wrap;
- [`docs/design/inventory.md`](docs/design/inventory.md) — per-class wrapping backlog.

Regenerate the design documents after bumping AFF3CT:

```bash
python3 scripts/gen_class_graph.py path/to/aff3ct/include docs/design
```
