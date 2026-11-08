# Installation

pyAFF3CT is compiled against pyStreamPU: both share the same StreamPU library and the same pybind11 version, so
pyStreamPU must be installed first, and pyAFF3CT built **without build isolation** in the same environment.

## Requirements

- Python ≥ 3.9, a C++17 compiler (GCC ≥ 9, Clang ≥ 10), CMake ≥ 3.18;
- [pyStreamPU](https://github.com/aff3ct/pystreampu) ≥ 1.2.1.

## Build

```bash
python -m venv .venv && . .venv/bin/activate
pip install "git+https://github.com/rtajan/pystreampu.git@v1.2.1"
pip install scikit-build-core setuptools_scm pybind11==3.0.4 pybind11-stubgen==2.5.5

git clone --recursive <pyaff3ct repository> && cd pyaff3ct
# or, in an existing clone:
git submodule update --init lib/aff3ct
git -C lib/aff3ct submodule update --init --recursive lib/cli lib/MIPP lib/date

pip install -v . --no-build-isolation
```

The first build compiles AFF3CT for every precision (8, 16, 32 and 64 bits): about 15 minutes on two cores.
`ARCH_FLAGS=-march=native` tunes it for the host (default on x86-64: `-msse4.2`).

The type stubs (`.pyi`, for the autocompletion of the IDEs) are generated from the compiled extension and
installed with the package when `pybind11-stubgen` is installed (CMake option `PYAFF3CT_STUBS`, on by default).
Point the IDE at the Python of the environment, and start Python outside the root of the repository: there,
`import aff3ct` would import the sources, which have neither the extension nor the stubs.

Check the installation:

```python
>>> import aff3ct as af
>>> enc = af.enc.repetition(4, 12)
>>> enc.K, enc.N
(4, 12)
```

## Optional data

The AFF3CT reference curves and configuration files (LDPC matrices, frozen bits...) are git submodules of AFF3CT;
the tests and some examples use them when they are present:

```bash
git -C lib/aff3ct submodule update --init refs conf
```

## Tests and documentation

```bash
pip install pytest pytest-xdist matplotlib
pytest tests -n 4                       # not `python -m pytest` from the root: the sources would shadow the package

pip install ".[docs]" --no-build-isolation
python scripts/doc_figures.py           # the figures of the documentation (a few tens of seconds)
mkdocs serve
```
