# Plan — pyaff3ct

Python wrapper (pybind11) of the [AFF3CT](https://github.com/aff3ct/aff3ct) library, built as an **extension of
[pystreampu](https://github.com/aff3ct/pystreampu)** (a separate package that depends on `streampu`), restarted from
scratch: the `_pyaff3ct` prototype serves as lessons learned (guidelines, code, see §2).

Related documents:

- [`docs/design/class_graph.md`](docs/design/class_graph.md): graph of all the classes to wrap (Mermaid, generated).
- [`docs/design/inventory.md`](docs/design/inventory.md): class-by-class inventory (strategy, priority, Python name, status).
- [`docs/design/status.json`](docs/design/status.json): wrapping status per class (`Kind::Name` → `todo`/`wip`/`done`), the only source edited by hand.
- [`docs/design/aff3ct_api.json`](docs/design/aff3ct_api.json): fingerprint of the reference AFF3CT API (see §7).
- [`docs/design/changes/`](docs/design/changes/): reports on the evolutions of AFF3CT.
- `scripts/`: `gen_class_graph.py` (graph + inventory), `aff3ct_api.py` (fingerprint), `aff3ct_diff.py` (comparison),
  `track_aff3ct.py` (tracking from one revision to another).

---

## 1. Goals

1. **Smooth Python interaction**, in the pystreampu philosophy: an AFF3CT module *is* a `streampu.Module`;
   its tasks are called like functions (`enc.encode(u)`), its sockets are read as `numpy`, and the chains
   run with `streampu.Sequence` / `streampu.Pipeline`.
2. **Factory-first but transparent**: creation goes through the AFF3CT factories whenever they exist, to keep
   the same behaviour as the `aff3ct` CLI (validation, default values, choice of the SIMD/template implementations),
   **without the user having to handle the factory**: they call a function that directly returns the module.
3. **Faithful inheritance**: each `py::class_` reproduces the C++ inheritance chain, StreamPU interfaces included.
4. **Clean separation**: C++ bindings in `internal/`, user API in `aff3ct/`.
5. **Exhaustive but driven coverage**: the generated inventory serves as the backlog, and each class goes from `todo` to `done`.
6. **Tooled tracking of AFF3CT**: each upstream change produces an impact report on the bindings (§7).

## 2. What we keep and what we change compared to `_pyaff3ct`

| `_pyaff3ct` guideline | Decision for `pyaff3ct` |
|---|---|
| `internal/include/internal/Wrapper/{Factory,Module,Tools}` tree + mirrored `internal/src/...` | **Kept** (`.hpp`/`.hxx`/`.cpp` rule included) |
| Factory-first | **Kept**, hardened (classes with a *policy* template only through a factory) **and made transparent** (R5) |
| Reproduced inheritance | **Kept**; the StreamPU bases are **imported** from pystreampu, never re-wrapped |
| Constructors "with classic types" | **Kept**; the AFF3CT types needed by the constructors (tools) are wrapped (see the `uses` edges of the graph) |
| One precision per build (implicit) | **Changed**: `AFF3CT_MULTI_PREC` build, type chosen at runtime through `dtype` (as pystreampu) |
| Hand-written list of classes | **Changed**: inventory generated from the headers, hence reproducible and checkable |

State of the `_pyaff3ct` prototype (reviewed): AFF3CT pinned at **v4.1.2** (`60e113d`); wrapped: `CRC`,
`CRC_polynomial(_fast/_inter)`, `Decoder`/`_HIHO`/`_SIHO`/`_SISO`, `Encoder`, `Modem`, `Sparse_matrix`, `Galois`,
`RS_polynomial_generator`, DVB-S2 constants, and the Encoder/Decoder factories (LDPC, polar, RS, RSC, RSC_DB) + Modem;
helpers `data_validator`, `str_operations`, `type_list`. The report
`docs/design/changes/v4.1.2_60e113d4..v4.7.2_e1b52965.md` lists what has moved since: to be reused knowingly
(helpers to review in phase 1, nothing to copy as is).

## 3. Target architecture

### 3.1 Dependencies and linking

```
aff3ct (Python)  ──import──▶  streampu (Python, pystreampu)
     │                              │
aff3ct._ext (pybind11)  ──py::module_::import("streampu")──▶  streampu._ext
     │                              │
libaff3ct (static, MULTI_PREC)      │
     └──────── link ──────▶  static libstreampu (exported by pystreampu, same commit)
```

Findings on pystreampu (local `develop`, `c7318f4`) that set the frame:

- StreamPU **v1.10.0 `85ed022`**, exactly the commit pinned by AFF3CT `develop` → the ABI of `Task`/`Socket`/`Module`
  is shared; `track_aff3ct.py` reports any future divergence.
- pybind11 pinned at **3.0.4** (dependency `pybind11>=3.0.4,<3.1`, *internals* v11): pyaff3ct uses the same constraint.
- Python ≥ 3.10, including **free-threaded 3.14t**: `PYBIND11_MODULE(_ext, m, py::mod_gil_not_used())` as pystreampu,
  and no unprotected mutable global data on the wrapper side.
- The official extension model (`examples/custom_cpp_module`) links **its own static copy** of StreamPU and calls
  `spu::tools::Buffer_allocator::set_task_autoalloc(true)` again at import: pyaff3ct follows this model (see risk 2).
- `streampu._ext.sfl` exposes `Stateful` (C++ `spu::module::Stateful`) and `Stateful_core` (Python modules).

- The compiled module `aff3ct._ext` calls `py::module_::import("streampu")` at initialization. The types
  `spu::module::Module`, `Stateful`, `Source`, `Sink`, `spu::runtime::Task`, `Socket`, the interfaces
  `spu::tools::Interface_*`, `Reporter`, `Terminal*` and `dtype` are **those of pystreampu**.
- AFF3CT is compiled as a **static library** (`AFF3CT_COMPILE_STATIC_LIB=ON`, `AFF3CT_COMPILE_EXE=OFF`,
  `-fPIC`, `AFF3CT_MULTI_PREC`), with **`AFF3CT_INCLUDE_SPU_LIB=OFF`**, to link the StreamPU exported by
  pystreampu (`streampu.get_cmake_dirs()`, as in `pystreampu/examples/custom_cpp_module`).
- The C++ helpers of pystreampu (`wrapper/Common/Tools/type_list.hpp`, `type_functions.h`, `Type.hpp`: `dtype`,
  `ALL_DTYPES`, `str2typeid`…) are reused from the headers installed by pystreampu.
- No registration mechanism with pystreampu (`streampu.plugins` no longer exists): `aff3ct` is a standalone
  package that declares `streampu` as a dependency and imports it; the integration relies only on sharing the
  pybind11 types (import of `streampu._ext` before the registration of the AFF3CT classes).

### 3.2 Build and packaging

- `scikit-build-core>=1.0` + `pybind11==3.0.4` (build) / `>=3.0.4,<3.1` (runtime) + `setuptools_scm`, C++17.
- `lib/aff3ct` as a pinned git submodule.
- CMake options exposed through `-Ccmake.define.*`: instantiated precisions, `AFF3CT_LINK_GSL/MKL`, `-march`.
- One compilation unit per family (`Encoder_polar.cpp`, `Decoder_LDPC.cpp`…) to parallelize and limit the RAM.
  `ccache` and `CMAKE_UNITY_BUILD` can be enabled as options.
- `cibuildwheel` (Linux x86_64/aarch64, macOS) in phase 5.

### 3.3 Tree

```
pyaff3ct/
├── CMakeLists.txt
├── pyproject.toml
├── lib/aff3ct/                       # AFF3CT submodule (pinned)
├── internal/
│   ├── include/internal/
│   │   ├── internal.hpp              # common includes, py::module_::import("streampu")
│   │   ├── Common/Tools/             # dtype dispatch, casters (vector<bool>, Sparse_matrix, Noise), keep_alive helpers
│   │   └── Wrapper/
│   │       ├── Module/<Domain>/<Class>.hpp|.hxx
│   │       ├── Factory/<Domain>/<Class>.hpp|.hxx
│   │       └── Tools/<Domain>/<Class>.hpp|.hxx
│   └── src/
│       ├── ext.cpp                   # PYBIND11_MODULE(_ext, m)
│       └── Wrapper/...               # exact mirror of include/
├── aff3ct/                           # Python API
│   ├── __init__.py                   # submodules, version (no dtype defined here)
│   ├── _dispatch.py                  # choice of the C++ instantiation from the dtypes
│   ├── crc.py chn.py dec.py enc.py ext.py itl.py mdm.py mnt.py pct.py qnt.py src.py cst.py
│   ├── factory/                      # factories (advanced use: from_cli, params); hidden by default
│   ├── tools/                        # polar, ldpc, itl, cst, gen, turbo…
│   ├── codec.py reporter.py interfaces.py
│   └── py.typed + *.pyi              # generated stubs (pybind11-stubgen)
├── tests/
├── examples/
├── docs/                             # mkdocs (as pystreampu); docs/design/* generated
└── scripts/                          # gen_class_graph, aff3ct_api, aff3ct_diff, track_aff3ct, gen_instantiations
```

Python submodules = AFF3CT factory prefixes (`crc`, `chn`, `cst`, `dec`, `enc`, `ext`, `itl`, `mdm`, `mnt`,
`pct`, `qnt`, `src`): they are the same as in the CLI (`--enc-type`, `--dec-implem`…), so nothing new to learn.

## 4. Wrapping strategy (rules applied by the inventory)

Figures taken from `docs/design/inventory.md` (AFF3CT `develop` @ `e1b5296`):

| Namespace | abstract | wrap | factory-only | functions | not exposed |
|---|---|---|---|---|---|
| `aff3ct::module` | 13 | 129 | 47 | – | – |
| `aff3ct::tools` | 23 | 66 | 16 (`Codec_*`) | 5 | 88 |
| `aff3ct::factory` | 1 | 83 | – | – | – |

**R1 — Inheritance.** `py::class_<T, Base, Interfaces...>`, where the StreamPU bases come from the imported module. Example:
`Encoder_polar<B>` → `Encoder<B>` → (`spu::module::Stateful`, `spu::tools::Interface_set_seed`) +
`tools::Interface_get_set_frozen_bits`. The AFF3CT interfaces (`Interface_get_set_frozen_bits`, `_noise`,
`_pretransform`, `_dynamic_frozen_bits`, `get_trellis`, `notify_noise_update`) are bound once, without a constructor.

**R2 — Abstract bases (blue).** `CRC`, `Channel`, `Coset`, `Decoder`/`_HIHO`/`_SIHO`/`_SISO`, `Encoder`,
`Extractor`, `Modem`, `Monitor`, `Puncturer`, `Quantizer`: no constructor. The common accessors are bound on them.
The tasks and sockets already exist at runtime: the access `mod.encode`, `mod["encode::U_K"]` and the call
`mod.encode(u)` come from the `streampu.Module` layer, without additional code.

*Accessor convention (as pystreampu)*: `get_X()` → read-only property `X` (`enc.K`, `enc.N`,
`enc.info_bits_pos`); `is_X()` and `set_X()` stay methods (`enc.is_sys()`, `dec.set_auto_reset(False)`,
`mdm.is_filter()`). No writable property on the modules. pystreampu reaches the tasks through
`Module.__getattr__` (fallback): an attribute named after a task would hide it (`Modem.filter`); a test
(`test_no_attribute_hides_a_task`) checks it for all the wrapped classes, from the tasks of the fingerprint.

**R3 — Templates and dtypes.** pyaff3ct **defines no data type**: the only dtypes are those of
pystreampu (`streampu.dtype`, `spu.int8`, `spu.int16`, `spu.int32`, `spu.int64`, `spu.float32`, `spu.float64`),
on the Python side as on the C++ side (`pyspu::dtype`, `pyspu::dtype::of<T>()`, `spu::runtime::type_to_string`,
`tl::type_list`). There is therefore no re-export, alias or conversion: a socket produced by an AFF3CT module has the
same `dtype` as a pystreampu socket, and `spu.int32(x)` / `socket.astype(spu.float32)` apply directly.
Mapping with `Tools/types.h`: `B_8/Q_8 → spu.int8`, `B_16/Q_16 → spu.int16`, `B_32 → spu.int32`,
`B_64 → spu.int64`, `R_8/R_16/R_32/Q_32 → spu.float32`, `R_64/Q_64 → spu.float64`. The unsigned dtypes of
pystreampu (`uint*`) are instantiated by no AFF3CT module: passing them raises an explicit `TypeError`.

A class template is instantiated **only for the combinations compiled by AFF3CT**
in `MULTI_PREC` (for instance `Modem_BPSK<B,R,Q>`: `(i8,f32,f32)`, `(i8,f32,i8)`, `(i16,f32,f32)`, `(i16,f32,i16)`,
`(i32,f32,f32)`, `(i64,f64,f64)`; `Decoder_*<B,Q>`: `(i8,i8)`, `(i16,i16)`, `(i32,f32)`, `(i64,f64)`).
`scripts/gen_instantiations.py` extracts these lists from the `explicit template instantiation` blocks of the `.cpp`
files, which avoids any missing symbol. On the C++ side, the classes are named `Encoder_polar_int32`,
`Modem_BPSK_int32_float32_float32` (pystreampu convention); on the Python side, the dtypes are given under the names
of the AFF3CT template parameters (`B=`, `R=`, `Q=`…), or `dtype=` when there is only one:

```python
import streampu as spu
enc = aff3ct.enc.polar(K, N, frozen_bits, B=spu.int64)              # -> _ext.enc.Encoder_polar_int64
mdm = aff3ct.mdm.bpsk(N, B=spu.int16, R=spu.float32, Q=spu.int16)
dec = aff3ct.dec.polar(K, N, frozen_bits, B=spu.int8)               # Q = int8: the only value compiled with B=int8
```

Resolution (`aff3ct/_dispatch.py`): the given dtypes are kept; a missing parameter takes the **only value
compatible** with the others when it is unique (`B=int8` ⇒ `Q=int8`), otherwise its **default**. The defaults of `B`,
`R` and `Q` are those of the 32-bit precision of the AFF3CT CLI (`B=int32`, `R=Q=float32`) and not the literal C++
defaults, which can designate a combination that is not compiled (`Quantizer<R = float, Q = int>`); `Q = R` is respected.
A missing or ambiguous combination raises a `TypeError` that lists the available combinations.

*Indexable templates*: each Python submodule groups the instances of a class template
(`_ext.enc.Encoder_int8` … `Encoder_int64`) into a `Template` object: `isinstance(enc, af.enc.Encoder)` whatever
`B`, `af.enc.Encoder[spu.int16]` for one instance, `af.dec.Decoder_SIHO[spu.int32, spu.float32]`. The suffixed names
stay in `aff3ct._ext`; the grouping is automatic (`aff3ct._dispatch.export`), so added classes appear without
Python code.

**R4 — Factory-only (orange).** The classes whose template carries *policy* parameters (`API_polar`,
`Update_rule`, `MAX`, function pointers `F/G/H`, `PSI`…) are not instantiated by the wrapper: the factory
chooses the implementation (`Decoder_polar` with `implem="FAST"`, `Decoder_LDPC` with `type="BP_HORIZONTAL_LAYERED"`
and `implem="NMS"`…). The result is returned under the most derived registered type (pybind11 polymorphism): for
example `Decoder_SIHO_int32_float32`, with all its tasks. The intermediate families without policies
(`Decoder_LDPC_BP`, `Decoder_RSC_BCJR`, `Decoder_turbo`…) are registered to expose their accessors (`n_ite`…).

**R5 — Transparent factories.** The user does not create a factory: they call the function of the family, which
returns the module ready to use. Internally: instantiation of the factory, assignment of the parameters passed as
keywords, `build` with the requested dtypes.

```python
dec = af.dec.polar(K, N_cw=N, frozen_bits=fb, type="SCL", implem="FAST", L=8)    # Decoder_SIHO ready to use
```

The parameters keep **the names of the attributes of the AFF3CT factories** (`N_cw`, `type`, `implem`, `n_ite`, `L`…),
with no translation table to maintain.

- Accepted keywords = public parameters of the factory (extracted in `aff3ct_api.json` with their defaults) +
  arguments of `build` (`frozen_bits`, `crc`, `encoder`…) + dtypes. Signatures, docstrings and stubs are **generated**
  from the fingerprint: an upstream change of a factory parameter appears in the tracking report and is carried over
  by regeneration.
- An unknown parameter raises a `TypeError` that lists the valid parameters (no silent assignment).
- Without a factory (simple class), the same function calls the constructor directly: the user does not see the
  difference.
- Advanced use, explicitly opt-in in `aff3ct.factory` (the functions are enough day to day):

  ```python
  f = af.factory.Decoder_polar.from_cli("--dec-type SCL --dec-L 8")   # on the class: creates the factory
  f.K, f.N_cw = K, N                                                  # parameters = attributes
  f.from_cli("--dec-implem NAIVE")                                    # on an instance: updates it
  dec = f.build(fb, B=spu.int16)                                      # builder chosen from the dtypes
  f.parameters, f.headers(), f.print_help(), f.clone()
  ```

  `from_cli` goes through the `cli::Argument_handler` parser of AFF3CT (exact parity with the CLI); an unknown argument
  or one of another factory raises a `ValueError`.

**R6 — Ownership and lifetime.**

- `build()` / constructors: `return_value_policy::take_ownership`.
- Objects kept by reference in a module: `py::keep_alive<1, n>()` on the constructor, and `<0, n>` on `build()`.
  Cases listed by the `uses` edges: `Interleaver(core)`, `Encoder_turbo(enc_n, enc_i, itl)`, `Decoder_turbo(siso_n, siso_i, itl)`,
  `Decoder_RA(itl)`, `Decoder_*_CA(crc)`, `Decoder_ML/chase(encoder)`, `Encoder_LDPC(G/H)`, `Decoder_LDPC_*(H)`,
  `Modem_generic(constellation)`, `Channel_*(generator)`, `Puncturer_polar(fb_generator)`. For each case, the C++
  source is checked for a copy or a reference, and a `gc.collect()` test covers it.
- `deep_copy` / `clone` of the modules (used by the multi-threaded `Sequence`): we check that the internal references
  are rewired (as AFF3CT does for `Decoder_turbo`) before exposing a module in multi-threading.

**R7 — Type conversions (smoothness).**

| C++ | Python |
|---|---|
| `std::vector<bool>` (frozen bits) | `numpy.ndarray[bool]` (and list accepted) |
| `std::vector<T>` / `std::vector<std::vector<T>>` | `numpy.ndarray` / list of lists |
| `tools::Sparse_matrix` | bound class + `to_scipy()` / `from_scipy()` / `from_dense()`; `aff3ct.tools.ldpc.read_alist(path)` |
| `tools::Noise<R>` (`Sigma`…) | bound class + a `float` accepted (`sigma=`) |
| `*_implem` enums (`STD`, `FAST`, `GSL`, `MKL`) | `py::enum_` + string accepted (`"FAST"`) |
| file paths | `str` or `os.PathLike` |
| functions `esn0_to_sigma`, `ebn0_to_esn0`, `sigma_to_esn0`, `esn0_to_ebn0` | `aff3ct.tools.*`, numpy-vectorized |

**R8 — Exceptions.** AFF3CT raises the `spu::tools::*` exceptions (`invalid_argument` ×313, `runtime_error` ×235…),
translated by pystreampu (`streampu.exceptions`). *Checked in phase 1* despite the static copy of StreamPU of
`aff3ct._ext`: an error raised in libaff3ct arrives as `streampu.exceptions.InvalidArgument` with the full AFF3CT
message (`test_aff3ct_exceptions_are_the_streampu_ones`). The errors of the wrapper itself are standard Python
exceptions (`TypeError` for unknown dtypes and parameters, `ValueError` for the CLI).

**R8 bis — Type of the modules returned by pystreampu.** pybind11 types a returned `Module*` (modules of a `Sequence`,
`task.module`…) after its exact dynamic type; if this concrete class is not registered
(`CRC_polynomial_fast<int>`, and above all the 47 "factory-only" classes), it falls back to `Module`: the tasks remain
usable but the AFF3CT accessors are lost. *Observed in phase 1*. **Decision and implementation**: a registry of
"downcasters" in pystreampu (merged into `develop`, header
`wrapper/Common/Tools/Module_downcast.hpp`) — a specialization of `pybind11::polymorphic_type_hook<spu::module::Module>`
that, for an unregistered dynamic type, queries the downcasters registered by the extensions (stored in the
*shared data* of the pybind11 internals, hence shared despite the copies of StreamPU; mutex for the free-threaded mode).
On the pyaff3ct side, each module `py::class_` calls `add_module_class<T>()` (bases first) and a single downcaster
returns the most derived registered class (`internal/Common/Tools/downcast.hpp`). Detection at compile time
(`__has_include`, `aff3ct._ext.HAS_STREAMPU_DOWNCAST_REGISTRY`): with a pystreampu without the registry, everything
works except this typing (`xfail` test). Tests: clones of a 2-thread `Sequence` typed `CRC_int16` with their
accessors; every registered module class is registered (`_N_MODULE_CLASSES`). The CI builds pystreampu
from `develop`; to do at its next release: require this version of streampu in `pyproject.toml`.

**R9 — Not exposed.** 88 tool classes (SIMD polar APIs, LDPC update rules, sorting networks, PRNGs, trees,
`Reorderer`, DVB-S2 constants, `Contents_*`…): these are implementation details chosen by the factories.

**R10 — Documentation.** `R"pbdoc(...)"` docstrings on every class, property and `build` (Google format, as
pystreampu); generated `.pyi` stubs; mkdocs pages generated from the inventory.

## 5. Target Python API (end-to-end example)

```python
import numpy as np
import streampu as spu
import aff3ct as af

K, N, ebn0 = 512, 1024, 2.5
sigma = af.tools.esn0_to_sigma(af.tools.ebn0_to_esn0(ebn0, K / N))

fb  = af.tools.polar.frozen_bits(K, N, sigma, method="GA_Arikan")   # np.ndarray[bool]
src = af.src.random(K, B=spu.int32)                                  # Source_random_fast<int32_t>
enc = af.enc.polar(K, N_cw=N, frozen_bits=fb)
mdm = af.mdm.bpsk(N)
chn = af.chn.awgn_llr(N, seed=42)
dec = af.dec.polar(K, N_cw=N, frozen_bits=fb, type="SC", implem="FAST")   # Decoder_polar factory, hidden
mnt = af.mnt.bfer(K, max_fe=100)

cp  = spu.array([sigma], dtype=spu.float32)          # channel parameter (CP socket)
u   = src.generate()[0]                               # generate -> (out_data, out_count), as pystreampu
y   = chn.add_noise(cp, mdm.modulate(enc.encode(u)))
v   = dec.decode_siho(mdm.demodulate(cp, y))
mnt.check_errors(u, v)

seq = spu.Sequence(mnt["check_errors::status"], n_threads=8)   # pystreampu API
seq.exec()                                              # stop: Monitor_BFER implements Interface_is_done
print(af.reporter.Reporter_BFER(mnt))
```

The names of the tasks and sockets are those of AFF3CT (`generate`, `encode`, `modulate`, `add_noise`,
`demodulate(CP, Y_N1)`, `decode_siho`, `check_errors`). Calls and bindings by position or by name follow the
rules of pystreampu. Two helpers remain to be created: `af.tools.polar.frozen_bits` (sugar on top of
`Frozenbits_generator_*`) and the stop of `Sequence.exec()` through the monitor (to be validated in phase 2;
otherwise, `exec_n_times` or a `stop_condition` to expose in pystreampu).

## 6. Roadmap

Each phase ends with an MR, and its **Definition of Done** includes: compilation OK, `pytest` green,
inventory updated (`done`), docstrings present.

### Phase 0 — Repository bootstrap ✅ (delivered with phase 1)
- `pyproject.toml` (scikit-build-core, `pybind11==3.0.4`, `streampu` required at build time), `CMakeLists.txt`,
  `lib/aff3ct` submodule pinned at `e1b5296` (v4.7.2) with its submodules `cli` (+ `rang`), `MIPP`, `date`.
- AFF3CT compiled as static `MULTI_PREC`, `AFF3CT_INCLUDE_SPU_LIB=OFF`, linked to the StreamPU installed by pystreampu
  (`find_package(cpptrace)` then `find_package(StreamPU)`, as `examples/custom_cpp_module`).
- Common SIMD baseline `PYAFF3CT_ARCH_FLAGS` (default `-msse4.2` on x86-64: MIPP stops at runtime with the
  SSE2 baseline, see AFF3CT `420db34`; `-march=native` for a local build).
- `scripts/dev_build.sh`: development build (`build/dev`) and link of `_ext` into `aff3ct/` for `pytest`.
- Left to do: CI (build + tests Linux/macOS) and check of the full `pip install .`.

### Phase 1 — Foundation (generic infrastructure) ✅
- `internal/include/internal/Common/Tools`: `combos.hpp` / `dtypes.hpp` (registration of one class per
  dtype combination, pystreampu suffixed names), `casters.hpp` (`std::vector<bool>` ↔ `numpy.ndarray[bool]`).
- `scripts/gen_instantiations.py` → `internal/include/internal/Generated/instantiations.hpp` and
  `aff3ct/_generated/instantiations.py`: compiled combinations (201 templates, 81 factory builders), 32-bit
  precision defaults.
- AFF3CT interfaces (6), 13 abstract module bases (R2 accessor convention), `Noise` / `Sigma` /
  `Event_probability` / `Received_optical_power`.
- `factory::Factory`: `from_cli` (class or instance), `parameters`, `headers`, `print_help`, `clone`, parameters as
  keywords, builders chosen from the dtypes; engine of the transparent factories `_factory.build`.
  Toy factory: `CRC` (builds real modules whose tasks run through pystreampu).
- `aff3ct/_dispatch.py`: dtype resolution and indexable `Template`s, automatic export per submodule.
- Tests: import, dispatch (`uint*` refused included), pystreampu inheritance, accessor convention, no
  attribute/task conflict, casters, noise, factory (keywords ≡ `from_cli`, errors, `headers`, `clone`, build per dtype,
  execution of the `build`/`extract` tasks of a CRC).

### Phase 2 — MVP: complete BFER chain (priority **P0**, 93 entries)
- **First** ✅: generator `scripts/gen_factories.py` (from `aff3ct_api.json`, `instantiations.py` and
  `status.json`) → one C++ unit per factory (79 factories, 88 builders: `def_param` parameters, sub-factories as
  references, builders per dtype, non-template builders as `_<builder>_raw`) and `aff3ct/_generated/functions.py`
  (55 family functions, exported by each submodule). Rules applied:
  - **Positional**: the sizes (`K`, `N_cw`, `N`) of the highest factory of the family that declares any
    (`Decoder` → `K, N_cw`; `Monitor_BFER` → `K`; the `N` of `Decoder_LDPC` stays a keyword), then the arguments of the
    builder; **keyword-only**: all the other parameters (`None` = AFF3CT default) and the dtypes (`B=`, `Q=`…).
  - **One builder = one function**: `polar` (`build`), `polar_siso`, `polar_gen`; the overloads of a builder
    (`Channel.build()` / `build(dist)`) are merged, pybind11 chooses from the given arguments.
  - Optional arguments: also bound as truncated overloads (pybind11 does not load `None` into a pointer of an
    unwrapped type); a non-literal default (`std::ostream& stream = std::cout`) is not exposed.
  - A function is generated only if the returned class is wrapped (module: a wrapped base is enough, thanks to the
    downcaster registry; tool: the exact type); the others are listed in `SKIPPED` (28: `Codec_*`,
    `Frozenbits_generator`, `Interleaver_core`, `Constellation`…) and will appear when these tools are wrapped.
  - `Codec` and `Decoder` (family bases) are bound without a constructor; `Terminal.build` is left out
    (`vector<unique_ptr<Reporter>>`, use `streampu.Terminal_std`).
  - AFF3CT convention to know: a bit is 0 or "non-zero"; the monitors compare as booleans.
    `aff3ct.tools.hard(x)` (socket or array) gives the 0 / 1 view. Measured by `scripts/probe_bit_convention.py`
    → `docs/design/bit_convention.md` (to rerun at each AFF3CT change): over 100 combinations
    (function × type × implem × dtypes), the encoders always return 0 / 1, and only the **FAST** polar decoders
    (SC, SCL, SCL_MEM, ASCL, ASCL_MEM) and **SCAN** return the sign bit for a 1 (`-128` in `int8`,
    `-2147483648` in `int32`), on `V_K` as on `V_N`; all decode correctly.
  - Default of the truncated overloads fixed: a later argument can be given without the earlier ones
    (`encoder=` without `crc=`), the literal defaults being kept.
  - **Interfaces of the concrete classes** ✅: a module built by a factory is typed after its most derived wrapped
    base (`Decoder_SIHO_int32_float32`); rather than registering each concrete class (the factories instantiate them
    with template parameters that are not exposed: `Decoder_polar_SC_fast_sys<B, Q, API_polar>`…), the
    accessors of an interface are bound on the bases whose children implement it (from the fingerprint:
    `Encoder` → `frozen_bits`, `dynamic_frozen_bits`, `pretransform`, `trellis`; `Decoder` → the first three;
    `Extractor` → `frozen_bits`) and reach the interface through `dynamic_cast`
    (`internal/Common/Tools/interfaces.hpp`). On a module that does not implement it, they raise `AttributeError`:
    `hasattr(dec, "frozen_bits")` tells whether the decoder uses frozen bits.
  - **Callable templates** ✅: `af.tools.Sigma(0.5)`, `af.itl.Interleaver(core, D=spu.float32)`; the keywords
    named after the template parameters (or `dtype=`) choose the instance, the others go to the constructor.
  - **Header-only modules** (`module::Interleaver<D, T>`): their dtype combinations come from the builders that
    return them (`gen_instantiations.py`); non-`const` `static` builders recognized (`Interleaver::build`).
  - Checked: chain source → `enc.polar` → BPSK → AWGN → `dec.polar` (SC NAIVE/FAST, `int8`/`int16`/`int32`) →
    `mnt.bfer`, CA-SCL with a CRC kept alive by the decoder, SISO SCAN.
- Modules (through the generated functions; checked: polar, LDPC, BCH, RS, repetition, RSC, BPSK, AWGN, BFER):
  `Source_random_fast`, `CRC_polynomial/NO`, `Encoder_{NO,polar,polar_sys,LDPC,LDPC_from_H,BCH,RS,repetition_sys}`,
  `Modem_BPSK(_fast)`, `Channel_{AWGN_LLR,NO}`, `Quantizer_{NO,pow2}`, `Decoder_{NO,repetition,BCH_std,RS_std}` +
  polar SC and LDPC BP through a factory, `Interleaver`, `Puncturer_NO`, `Monitor_BFER`.
- Tools ✅: `Sparse_matrix` (from/to NumPy, `__array__`, `to_scipy` / `from_scipy`, `T`, `turn`…), `AList`, `QC`,
  `LDPC_matrix_handler` (`read` → `(H, info_bits_pos, pct_pattern)`, `transform_H_to_G`), `Galois`,
  `BCH_polynomial_generator`, `RS_polynomial_generator`, `Frozenbits_generator_{GA_Arikan,BEC,file}`
  (`gen.generate(noise)` → array of booleans), `Interleaver_core_*` (the 12 cores, all the `T`) + module
  `aff3ct.itl.Interleaver`, `Sigma` + conversions (`ebn0_to_esn0`, `esn0_to_sigma`…, `sigma_from_ebn0`),
  `Reporter_{BFER,noise,throughput}` (with `spu.Terminal_std`), module `Monitor_BFER` (counters `n_fe`, `ber`, `fer`…,
  `collect`, callbacks).
  Notes: in AFF3CT, `sigma_to_esn0` is not the inverse of `esn0_to_sigma` (3.01 dB gap, factor 2);
  `H` is stored vertically (N rows, as the AList files), the `type="LDPC_H"` encoder computes G itself
  and gives `info_bits_pos` to the decoder; the sizes of `enc.rs` / `dec.rs` are in symbols.
- Fingerprint: comment `strip` fixed (a `//` inside a `/* … */`, here a URL, hid its end): two
  classes were missing (`RS_polynomial_generator`, `Decoder_RS_std`).
- **Numerical validation** ✅ (`tests/test_references.py`, < 2 s): polar SC (128, 96) GA, BCH (127, 106) t = 3 and
  LDPC CCSDS (128, 64) BP SPA with 50 iterations, compared with the `lib/aff3ct/refs` references (FER within 4
  binomial standard deviations); the CI fetches `refs` and, from `conf`, the only matrix used.
- Example ✅ `examples/polar_bfer.py` (multi-threaded `streampu.Sequence`, `Terminal_std`, frozen bits adapted to the
  noise through `set_frozen_bits` on the clones). Remaining: `examples/ldpc_bfer.py` and a notebook.
- Found on the pystreampu side, fixed in v1.2.1 (required): `Terminal_std(reporters)` did not keep its reporters
  alive; `stop_temp_report` was bound to `start_temp_report`. `Sequence(task)` takes the task as the **first** one
  (pass it through an end socket: `Sequence(mnt["check_errors::status"])`).
- **Multi-thread reduction** ✅: with `Monitor_BFER`, each thread has its clone and the sequence stops as soon as
  **one** clone reaches `max_fe` (reduced FER biased upwards; the original counts at best the frames of the first
  thread).
  Class specific to pyaff3ct, temporary, after the `Monitor_BFER_AR` of py_aff3ct:
  `internal/include/internal/Module/Monitor/BFER_AR/Monitor_BFER_AR.hpp` → `af.mnt.Monitor_BFER_AR(K, max_fe)`.
  It derives from `Monitor_BFER<B>` (the reporters and accessors remain valid); its clones share totals
  (mutex) copied into the clone and into the original at each frame, `is_done()` reads the totals again, `reset()`
  zeroes them. The pyaff3ct classes are declared in `PYAFF3CT_TEMPLATES` (`_dispatch.py`) for the
  grouping by dtype. Checked: 4 threads → total FE = `max_fe` (+ frames in flight), FER consistent with the polar
  reference. To remove if AFF3CT / pystreampu offer the equivalent (`Monitor_reduction`).

### Phase 3 — Core coverage (priority **P1**, 229 entries) ✅
- All the remaining "mainstream" families: Turbo/RSC (+ `Post_processing_SISO`, `Flip_and_check`, `Scaling_factor`),
  RA, Repetition, Conv/Viterbi, Polar SCL/ASCL/SCF/SCAN, LDPC (all the rules through a factory), generic modem
  (`Constellation_*`), OOK, Rayleigh, BEC/BSC, `Extractor_*`, `Puncturer_*`, `Quantizer_custom`, noise generators.
- `Codec_*` (through factories): properties `encoder`, `decoder_siso`, `decoder_siho`, `extractor`, `puncturer`.
- **Codecs** ✅ (during phase 3): submodule `aff3ct.codec`, one function per family (`polar`, `ldpc`, `turbo`,
  `turbo_db`, `turbo_product`, `bch`, `rs`, `rsc`, `rsc_db`, `conv`, `ra`, `repetition`, `uncoded`, `polar_mk`,
  `polar_pac`, `polar_pt`); `Codec_*` classes (bases `Codec`, `Codec_HIHO/SIHO/SISO`) with the modules as properties
  (`encoder`, `decoder_siho`, `decoder_siso`, `puncturer`, `extractor`, `interleaver`; `None` if absent), which keep
  the codec alive, and their own accessors (`frozen_bits`, `trellis`, `H`, `GF`…).
  - Signature: `K`, `N_cw` and the arguments of the builder (`crc`) positional; `N` (frame size: a value other
    than `N_cw` adds the puncturer); the parameters of the sub-factories **prefixed** with the name of the
    sub-factory, as the command-line options (`dec_type`, `dec_L`, `enc_systematic`, `fbg_noise`,
    `pct_pattern`, `itl_core_type`…); sibling sub-factories with the same CLI prefix are set together
    (`enc_sub_standard` → `enc.sub1` and `enc.sub2`, as `--enc-sub-std`); dtypes `B=`, `Q=`.
  - As the dynamic types of the sub-factories are known only at runtime, the functions are built at
    import (`aff3ct/codec.py`, from the generated `CODECS`): `inspect.signature` and `help()` list them all.
    `af.codec.turbo.factory(...)` (same arguments) returns the configured factory (`headers()` as the simulator).
  - The parameters are those of the factories: a CLI option that sets several of them must be translated
    (`--dec-sf-type` → `dec_sf_enable=True, dec_sf_type=...`); `from_cli` remains available.
  - `cdc.set_noise(noise)` acts on the modules of the codec, not on their clones in a multi-threaded `Sequence`
    (adaptive frozen bits: `set_frozen_bits` on the clones, as `examples/polar_bfer.py`).
  - Generator: template factories with default arguments bound (`Decoder_turbo<>`, `Encoder_turbo<>`: `dec_n_ite`,
    `dec_sub_*`, `dec_sf_*`…), their builders taking the combinations of the returned module; `enable_puncturer` bound.
  - Validated against `refs`: RA (4096, 1024) MS 10 iterations and turbo LTE (K = 2048, CRC 24-LTEA, puncturing
    `11,10,01`, 8 iterations, LTE_VEC scaling factor), on 4 threads; `examples/ldpc_bfer.py` (LDPC codec).
- **Modems and channels** ✅: `Constellation_{PAM,PSK,QAM,user}` (`symbols` as a complex array, `bps`…);
  `af.mdm.modem(N, type="QAM", bps=4)` builds (and keeps) the constellation of the generic types, as the
  simulator, and a given constellation sets the type; `af.mdm.modem(N, symbols=...)` for an arbitrary
  constellation without an object or a file (protected constructor `Constellation(symbols, name)` of AFF3CT, exposed by
  `af.tools.Constellation(symbols, normalize=True)`; symbol `i` = image of the bits of `i`, first bit least
  significant); `mdm.N_mod` gives the size of the channel. AWGN,
  Rayleigh (`add_noise_wg` → `demodulate_wg`, `complex=True`), BEC and BSC channels (`OOK` modem with `channel_type`,
  monitor `count_unknown_values=True` as the simulator for an EP noise) validated against `refs` (uncoded: 16-QAM AWGN,
  QPSK Rayleigh, OOK BEC / BSC, BER within 5 standard deviations). Generator: the header-only tool templates that
  pass their parameters to their base take its combinations (`Constellation_QAM<R>`).
- **Polar decoders and tools** ✅: `Polar_code` (single / multi-kernel), `Frozenbits_generator_{GA,RM,5G,TV}`,
  `Pretransform_generator(_file)`. `from_cli(args, strict=False)`: a full AFF3CT command line given to
  each factory, which takes only its own arguments. `tests/test_references.py` rebuilds the chains **from the
  command line of the references** (source, CRC, codec, modem, channel; sizes propagated and AZCW as
  `BFER_std.cpp`, puncturer enabled as the polar / turbo / LDPC launchers): shortened polar CA-ASCL,
  Viterbi, BCJR, repetition, LDPC BP flooding SPA / AMS (min, min*), layered NMS, Gallager A / B / E, WBF, MWBF,
  LDPC NMS on BEC and BSC (EP noise). The CI fetches the 4 matrices used.
  Left without a function: `Scaling_factor`, `Flip_and_check` (post-processing internal to the turbo decoders, set
  by the codecs: `dec_sf_*`, `dec_fnc_*`).
- **Closing of phase 3** ✅:
  - **Build after `from_cli`**: `_complete()` (the AFF3CT `store()` on an empty command line) lost what
    AFF3CT derives only when reading the command line (frame size of the puncturer from `-N`, BCH sizes
    from `-T`). The arguments of the `from_cli` calls are recorded (`_CLI`, per factory) and replayed at build time
    (`_complete_cli`), then the parameters changed since the last `from_cli` are applied again. Without a command
    line, a BCH `t` consistent with the sizes is kept (`n_rdncy(N, t) = N - K`).
  - **Fixed precisions**: 8 and 16-bit chains (`-p`) with a quantizer after the demodulator, as
    `Simulation_BFER_std.cpp` (quantization defaults of the launchers); Eb/N0 conversion with the number of bits per
    symbol of the modem (`Noise.cpp`).
  - **References checked from their command line** (33, `tests/test_references.py`, ~80 s sequentially):
    polar SC 8/16 bits, SCAN 16 bits, RSC 8/16 bits, repetition 8/16 bits, double-binary RSC (DVB-RCS2),
    double-binary turbo (DVB-RCS1 / RCS2: QPSK, CRC, adaptive scaling factor, flip and check; BEC), product codes
    (extended BCH, Chase-Pyndiah), algebraic BCH and RS (AWGN, BSC, BEC), in addition to the previous ones.
  - Extractors and puncturers: base accessors (`K`, `N`, `N_cw`, `frozen_bits` of the polar puncturer and of the
    extractor); no other useful specific accessor (patterns set by the factories).

- DoD: one construction and execution test per class, and one CLI parity test per factory.

### Phase 4 — Advanced (priority **P2**, 51 entries) ✅
- Polar MK / PAC / PT (`Polar_code`, `Pretransform_generator`), SCMA, CPM, optical (`Distributions`), `Channel_user*`,
  EXIT/MI monitors and their reporters, Turbo product, AVX/SSE variants, `Monitor_reduction` (multi-thread).

Progress:
- ✅ **4A — MK, PAC, PT polar codes**: codecs `af.codec.polar_mk / polar_pac / polar_pt` validated on 8 AFF3CT
  references rebuilt from their command line (SC, SCL, ASCL CRC32, systematic, Fano); `conf/cde` files fetched
  by `scripts/fetch_aff3ct_data.sh`; example `examples/polar_variants.py`, section of the polar guide.
- ✅ **4B — SCMA, CPM**: modems validated on 5 uncoded references (SCMA AWGN and Rayleigh, CPM `k/p` and GSM) and
  one turbo + SCMA reference, built from their command line. As the simulator: `-F` (frames per
  execution; SCMA: one per user, imposed by the modem), `add_users` channel for SCMA, `filter` task of the
  CPM modems before the demodulation. Codebooks `conf/mod/SCMA`; example `examples/scma_cpm.py`, section of the guide.
  The iterative references (`--sim-type BFERI`, LDPC + CPM) are covered in phase 5.
- ✅ **4C — optical channel, "user" channels**: `af.tools.Distributions` (densities read from a file, `Distribution`,
  `Distribution_mode`): the builders of the channel and of the modem that take it are bound again (`af.chn.channel(N,
  dist, type="OPTICAL")`, `af.mdm.modem(N, None, dist, ...)`); 2 LDPC references on the optical channel (ROP noise)
  rebuilt from their command line; channels `USER`, `USER_ADD`, `USER_BEC`, `USER_BSC`, `RAYLEIGH_USER` tested
  (`tests/test_user_channels.py`); example `examples/optical.py`, sections of the guide.
- ✅ **4D — MI and EXIT monitors**: `Monitor_MI`, `Monitor_EXIT`, `Reporter_MI`, `Reporter_EXIT` bound
  (`af.mnt.mi(N, n_trials=...)`, `af.mnt.exit(size, ...)`; `size` becomes positional as `N`, except for the
  CRC); `af.mnt.reduce(seq, mnt)` sums the measures of the clones (role of `Monitor_reduction`, whose static loop,
  specific to the simulator, is not bound); measured BI-AWGN capacity = theory (`examples/mutual_information.py`,
  figure), EXIT checked on Gaussian LLRs (J function); "Monitors" guide.
- ✅ **4E — remaining modules**: reached through the factories and tested (`tests/test_p2_modules.py`): AZCW,
  coset and user encoders (`af.enc.encoder(K, N, type=...)`), BCH genius decoder (= algebraic decoder), list Viterbi
  (PLVA: 2 references), inter/intra-frame SIMD BCJR (int8 / int16), bit-packed polar encoder (= naive), DVB-S2 LDPC
  encoder, optical OOK with ROP estimation; turbo product modules through the codec (TPC references).
  These modules stay `todo` in `status.json` (`done` = own registered Python class): they are built by
  the factories and typed after their wrapped base class, as the decoders of phase 3.

**Closing of phase 4**: 52 AFF3CT references rebuilt from their command line (62 reference tests in
total), 249 tests. Left out of scope: `Decoder_RS_genius`, unusable in AFF3CT v4.7.2 (it only overrides the old hard
decoding without a status; strict `xfail` test that will report an upstream fix), the iterative simulations
`--sim-type BFERI` (done in phase 5) and `Monitor_reduction` (its static loop is specific to the simulator;
`af.mnt.reduce` takes its place).

### Phase 5 — Industrialization (priority **P3** included)
- mkdocs docs (generated API, guides, examples gallery) ✅, `.pyi` stubs ✅, `cibuildwheel` wheels.
- **Publication on PyPI: not yet** (maintainer's decision); the GitHub repository and the documentation are
  public. The wheels will be prepared (metadata, `twine check`, publication job written but disabled).
- Versions: `vX.Y.Z` tags on `main` (`setuptools_scm`), `CHANGELOG.md` (Keep a Changelog), procedure in
  `docs/development.md`; `v0.1.0` = phases 0 to 3 and documentation.
- Chosen order: versions and changelog, P3 debug tools, `BFERI` iterative simulations, throughput comparison
  with the native simulator; then wheels, macOS CI and PyPI preparation.
  - **Documentation (advanced, in English)**: MkDocs Material + mkdocstrings (`mkdocs.yml`, `docs/`, excluding
    `docs/design/`). The code of the pages is included from `examples/*.py` between `# --8<-- [start:x]` /
    `[end:x]` markers (pymdownx.snippets); the examples are run and checked by `tests/test_examples.py` (theory or
    AFF3CT references within 4 standard deviations), the `>>>` blocks of the pages by `tests/test_docs.py`. The figures
    (`docs/assets/figures/*.svg`, not versioned) are computed by `scripts/doc_figures.py`. CI: `docs` job
    (`mkdocs build --strict`, `public/` artifact) and `pages` (default branch). Pages: home, installation,
    tutorial (first chain, BER/FER curves, codecs, factories and command line), guides (polar, LDPC,
    turbo, modems and channels, fixed point), concepts, API reference, development.
- Debug tools: ✅ `Histogram` (also the histogram of `Monitor_MI`), `Frame_trace` (text returned instead of
  written to `std::cout`, invisible from notebooks), `Dumper` (frames in error); "Debugging" guide. Not bound:
  `Dumper_reduction` (takes ownership of `unique_ptr`s), GSL/MKL generators (AFF3CT compiled without these
  libraries).
- Iterative simulations: ✅ turbo demodulation (`BFERI`): sequence loop with the `Switcher` and `Iterator` of
  StreamPU, bound in Python style (`spu.Task.call_auto_exec = False` during the bindings);
  `af.tools.reset_decoders_on_check(seq)` (SISO decoders without automatic reset, reset after each
  frame checked by the monitor of the thread, as `Simulation_BFER_ite`); 2 LDPC (4224, 2112) + GMSK references
  rebuilt from their command line (coset approach, `USER` interleaver); example
  `examples/turbo_demodulation.py` (real encoder, no coset), "Iterative receivers" guide.

## 7. Tracking the evolutions of AFF3CT

Principle: the AFF3CT API the bindings depend on is reduced to a versioned **fingerprint**
(`docs/design/aff3ct_api.json`, produced by `scripts/aff3ct_api.py`). For each class: header, template
parameters, bases, constructors (types **and** default values), public methods, public parameters of the factories
(with defaults), tasks and sockets (direction, type, order — the order drives the positional Python call),
`MULTI_PREC` instantiations (classes and `build<…>`, hence the available dtype combinations); plus the commits of the
StreamPU and cli submodules.

Comparing two fingerprints (`aff3ct_diff.py`) classifies each change:

| Level | Examples | Consequence |
|---|---|---|
| Breaking | class/constructor/method/task/socket/parameter/instantiation removed or modified, base changed, header moved | binding or Python API to modify |
| Defaults | default value modified (constructor, factory parameter, `build`) | Python defaults to align |
| Addition | new class (with its computed strategy and priority), constructor, parameter, task, instantiation | backlog |
| Reorganization | method now inherited from a base | quick check |

Each change is crossed with `status.json`: a breaking or default change on a `done`/`wip` class is
a **required action**, put at the top of the report; `--fail-on-impact` then makes the exit code 1 (CI).

Usage:

```bash
# What is new upstream since the pyaff3ct reference?
python3 scripts/track_aff3ct.py --repo lib/aff3ct --fetch --to origin/develop
# Accepted upgrade: new reference + regenerated graph and inventory
python3 scripts/track_aff3ct.py --repo lib/aff3ct --to <ref> --update
```

The revisions are extracted into temporary `git worktree`s: the working submodule is never touched.

Validated on two real cases:
- `v4.1.2 → v4.7.2` (gap `_pyaff3ct` → today): 13 breaking (`Syndrome_checker` added to the LDPC BP decoders,
  Viterbi moved from `RSC/` to `Conv/`, `Encoder_polar_PAC` inheriting from `Encoder_polar`…), 1 default, 42 additions;
- `ec05893^ → v4.7.2` (Polar PT + bitpacked encoder): 1 breaking, 24 additions, 3 reorganizations, StreamPU change
  reported.

Proposed organization:
1. **Scheduled CI (weekly)**: `track_aff3ct.py --fetch --to origin/develop --fail-on-impact`; the report is
   published as an artifact, and an issue is opened (or updated) if there are changes.
2. **Submodule upgrade** = a dedicated MR containing: bump of `lib/aff3ct`, `--update` (fingerprint, graph,
   inventory), the report in `docs/design/changes/`, and the binding fixes for each required action.
3. **Consistency test** (from phase 1): each `done` class of `status.json` must exist in `aff3ct._ext` with
   tasks/sockets matching the fingerprint; a wrapped class missing from `status.json` also makes the test fail.
4. StreamPU alignment: the report flags any change of the StreamPU submodule of AFF3CT, to be compared with the commit
   pinned by pystreampu before accepting the upgrade.

## 8. Testing strategy

| Level | Content |
|---|---|
| Unit | construction for each pystreampu dtype combination; `uint*` refused; properties; errors (`TypeError` dtype, `ValueError` parameters) |
| Tasks | execution of a task on known `numpy` inputs (e.g. systematic encoder: `U == X[sys]`) |
| Factory | `build()` vs direct construction; `from_cli()` vs Python parameters; `params` vs `get_headers` |
| Lifetime | creation of dependent objects, deletion of the Python references, `gc.collect()`, execution |
| Multi-thread | `Sequence(n_threads>1)` on a complete chain (checks clone/deep_copy) |
| Numerical | BER/FER vs AFF3CT `refs/` on a few Eb/N0 points (`@pytest.mark.slow` marker) |

## 9. Risks and open points

1. **StreamPU version**: *resolved to date* (pystreampu and AFF3CT on `85ed022`, v1.10.0); monitored by the tracking (§7).
2. **Two static copies of StreamPU** (official extension model): `set_task_autoalloc` called again at import.
   *Checked in phase 1*: exception translation, multi-threaded `Sequence` (clones of AFF3CT modules) and typing of the
   modules returned by pystreampu (R8 bis, downcaster registry, merged into pystreampu `develop`).
   Beware: reinstalling streampu touches the StreamPU headers AFF3CT depends on, hence a full recompilation
   of AFF3CT (~15 min on 2 cores) at the next build.
   pystreampu v1.2.1 (required by `pyproject.toml`, `PYSTREAMPU_REF` of the CI): downcast registry published,
   `streampu.Stateful` exported, bounded socket indexing (`IndexError`, end of `iter(socket)`),
   `Terminal_std` keeping its reporters, `stop_temp_report` fixed.
3. **pybind11 ABI**: same constraint as pystreampu (`>=3.0.4,<3.1`, same compiler and stdlib), checked in CI.
4. **Compilation time and binary size**: about 190 classes × 4 to 6 instantiations. Levers: one TU per family,
   CMake option to restrict the precisions (`PYAFF3CT_PRECISIONS=32` in dev), ccache, LTO only in release.
5. **Internal references and `clone()`**: some modules (turbo, CA) keep references to other objects;
   to audit family by family (R6).
6. **Optional dependencies** (GSL, MKL, MPI): disabled by default, exposed only if compiled.
7. **AFF3CT evolution**: covered by §7; known limit: the fingerprint is extracted by textual analysis of the
   headers (no compiler), so an unusual C++ construct can escape the diff — the consistency tests
   (§7, point 3) act as a safety net.
8. **Free-threaded (3.14t)**: the AFF3CT modules run by a multi-threaded `Sequence` do not call Python; the only
   Python callbacks (reporters, stop conditions, `reset_decoders_on_check`) take the GIL back as in pystreampu.

## 10. Contribution conventions

- Branches `feat/<domain>-<family>`, `fix/...`; one MR per family or phase.
- Commit messages in the imperative mood, prefixed with the domain (`enc: wrap Encoder_polar`, `factory: add Decoder_LDPC build`).
- Every MR updates `docs/design/status.json` (then regenerates `inventory.md`) and adds its tests.
- MR checklist (taken from the guidelines): include/src mirror respected, compilation and import OK, Python API
  documented, tests added, correct paths and class names in the docs.
