# pyaff3ct

Python bindings (pybind11) for [AFF3CT](https://github.com/aff3ct/aff3ct), built on top of
[pystreampu](https://github.com/aff3ct/pystreampu): every AFF3CT module is a `streampu.Module`,
its tasks are callable from Python and its sockets are exposed as NumPy arrays.

Status: phase 2 in progress (generated module-level functions for every factory, P0 tools, BER/FER validated against
the AFF3CT references) — see `Plan.md`.

## Development build

Requires an environment where `streampu` (pystreampu) >= 1.2.1 is installed: pyaff3ct is built against its pybind11
and StreamPU versions. streampu is not on PyPI yet, so build without isolation:

```bash
pip install "git+https://github.com/rtajan/pystreampu.git@v1.2.1"      # or a local clone of pystreampu
pip install scikit-build-core setuptools_scm pybind11==3.0.4
git submodule update --init lib/aff3ct
git -C lib/aff3ct submodule update --init --recursive lib/cli lib/MIPP lib/date

pip install -v . --no-build-isolation            # install
pytest tests                                     # (not `python -m pytest` from the root: the sources shadow it)

PYTHON=path/to/python scripts/dev_build.sh       # or development build: build/dev, aff3ct/_ext*.so linked in the
path/to/python -m pytest                         # source tree

# optional: BER/FER references (tests/test_references.py, skipped without them)
git -C lib/aff3ct submodule update --init refs
```

The first build compiles AFF3CT in multi-precision (about 15 minutes on 2 cores). `ARCH_FLAGS=-march=native`
tunes it for the host (default on x86-64: `-msse4.2`).

```python
import streampu as spu
import aff3ct as af

K, N = 96, 128
fb = af.tools.Frozenbits_generator_GA_Arikan(K, N).generate(af.tools.sigma_from_ebn0(2.0, K / N))
src, enc = af.src.source(K, type="RAND"), af.enc.polar(K, N, fb)
mdm, chn = af.mdm.modem(N, type="BPSK"), af.chn.channel(N, type="AWGN")
dec, mnt = af.dec.polar(K, N, fb, type="SC", implem="NAIVE"), af.mnt.bfer(K, n_frame_errors=100)

sigma = spu.array([0.7], dtype=spu.float32)
u = src.generate()[0]                                     # AFF3CT tasks executed (and bound) by pystreampu
dec.decode_siho(mdm.demodulate(sigma, chn.add_noise(sigma, mdm.modulate(enc.encode(u)))))
mnt.check_errors(u, dec["decode_siho::V_K"])
spu.Sequence(mnt["check_errors::status"]).exec()          # until 100 frame errors
print(mnt.fer, mnt.ber)
```

With several threads, each thread runs clones of the modules: use `af.mnt.Monitor_BFER_AR(K, max_fe)`, whose clones
share their counters (the sequence stops on the total, and `mnt` shows it). See `examples/polar_bfer.py` for an SNR
loop with a `streampu.Terminal_std`.

Codecs build and connect the modules of a code family; the parameters of their sub-factories are prefixed as the
command-line options (`--dec-type` → `dec_type`):

```python
cdc = af.codec.turbo(K, 3 * K + 12, enc_sub_standard="LTE", dec_n_ite=8, dec_sub_implem="FAST")
enc, dec, itl = cdc.encoder, cdc.decoder_siho, cdc.interleaver
help(af.codec.turbo)      # every parameter
```

See `examples/ldpc_bfer.py`.

## Design documents

- [`Plan.md`](Plan.md) — architecture, wrapping rules and roadmap;
- [`docs/design/class_graph.md`](docs/design/class_graph.md) — graph of the classes to wrap;
- [`docs/design/inventory.md`](docs/design/inventory.md) — per-class wrapping backlog.

Regenerate the design documents after bumping AFF3CT:

```bash
python3 scripts/gen_class_graph.py path/to/aff3ct/include docs/design
```
