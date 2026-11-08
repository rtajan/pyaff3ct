# Changelog

All notable changes of pyAFF3CT. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
versions [Semantic Versioning](https://semver.org/) (0.x: the API may still change between minor versions). The
version of a build comes from the git tags (`setuptools_scm`): between two tags, `X.Y.Z.postN+gHASH`.

## [Unreleased]

### Added

- `af.tools.seed_sequence(seq, seed=0)`: a different seed in every module with a seed of every thread of a
  `streampu.Sequence`, as the AFF3CT simulator.
- Return types of the module functions (`af.dec.polar(...)` is a `Decoder_SIHO`) and class templates declared as the
  union of their classes in the stubs: the IDEs complete the returned modules.
- Multi-kernel, PAC and pre-transformed polar codes validated on AFF3CT references (`af.codec.polar_mk`,
  `polar_pac`, `polar_pt`); example `examples/polar_variants.py`.
- SCMA and CPM modulations validated on AFF3CT references; example `examples/scma_cpm.py`.
- Optical channel: `af.tools.Distributions` (noise densities read from a file), given to `af.chn.channel` and
  `af.mdm.modem`; channels whose noise, erasures, flips or gains come from a file (`USER`, `USER_ADD`, `USER_BEC`,
  `USER_BSC`, `RAYLEIGH_USER`); example `examples/optical.py`.
- Mutual information and EXIT monitors (`af.mnt.mi`, `af.mnt.exit`), their reporters (`Reporter_MI`,
  `Reporter_EXIT`) and `af.mnt.reduce(seq, mnt)`, the measures of all the threads in one monitor; example
  `examples/mutual_information.py`, guide *Monitors*.
- Tests of the remaining modules: all-zero, coset and user encoders, BCH genius decoder, list Viterbi decoder,
  SIMD BCJR decoders, bit-packed polar encoder, DVB-S2 LDPC encoder, OOK optical modem with ROP estimation.
- Debug tools: `af.tools.Histogram` (also the histogram of `Monitor_MI`, `mnt.mutinfo_hist`), `af.tools.Frame_trace`
  (text view of frames, returned as a string), `af.tools.Dumper` (frames in error recorded and written to files);
  example `examples/debugging.py`, guide *Debugging*.
- Iterative receivers (turbo demodulation, the `BFERI` simulations of AFF3CT): loop of a sequence with the
  `Switcher` and `Iterator` of StreamPU, `af.tools.reset_decoders_on_check(seq)` (the SISO decoders keep their
  state across the iterations of a frame); example `examples/turbo_demodulation.py`, guide *Iterative receivers*.
- 21 more AFF3CT references rebuilt from their command lines (54 in all, 2 of them iterative);
  `scripts/fetch_aff3ct_data.sh` fetches their configuration files.

### Changed

- `size` is positional, as `N`, in the module functions (`af.mnt.exit(size)`, `af.qnt.quantizer(size)`,
  `af.tools.interleaver_core(size)`), except for the CRC (its length); `size=` keeps working.
- `af.chn.channel` and `af.mdm.modem` take a `dist` argument again (optical channel).

### Fixed

- Multi-threaded simulations: the threads of a sequence drew the same frames and the same noise (copied random
  generators); the examples, the README and the tests call `af.tools.seed_sequence`.

### Known issues

- The RS genius decoder of AFF3CT v4.7.2 cannot be used (it redefines only the hard-input decoding without status).
- Iterative simulations (`--sim-type BFERI`, demodulation-decoding loop) are not covered yet.

## [0.1.0] - 2026-11-08

First version: the core of AFF3CT (phases 0 to 3 of `Plan.md`) and the documentation.

### Added

- Build against pyStreamPU (scikit-build-core, pybind11, AFF3CT compiled for 8, 16, 32 and 64 bits); every AFF3CT
  module is a `streampu.Module`, its tasks Python methods, its sockets NumPy arrays.
- Module functions generated from the AFF3CT factories for every family (`af.src`, `af.crc`, `af.enc`, `af.pct`,
  `af.itl`, `af.mdm`, `af.chn`, `af.qnt`, `af.dec`, `af.mnt`, `af.cst`, `af.ext`, `af.snk`), class templates
  grouped by dtype (`af.dec.Decoder_SIHO[spu.int16, spu.int16]`).
- Codecs of every code family (`af.codec.polar`, `ldpc`, `turbo`, `turbo_db`, `turbo_product`, `bch`, `rs`, `rsc`,
  `rsc_db`, `ra`, `repetition`, `uncoded`...), with the parameters of the AFF3CT command line as keywords
  (`--dec-type` → `dec_type`).
- Factories (`af.factory`), configurable with an AFF3CT command line (`from_cli`, `strict=False`).
- Tools: frozen bits generators, LDPC matrices (AList, QC), Galois fields, interleaver cores, constellations
  (modems from any list of symbols, `bit_order`), noises and conversions (`sigma_from_ebn0`), reporters.
- Fixed point (8 and 16 bits), generic modems, Rayleigh, BEC and BSC channels.
- `Monitor_BFER_AR`: BFER monitor whose clones share their counters (multi-threaded stop criterion).
- 33 AFF3CT reference curves rebuilt from their command lines and checked by the test suite.
- Documentation (MkDocs): tutorial, guides, concepts, API reference; its examples and `>>>` blocks are run by the
  tests, its figures computed at each build; GitLab Pages and GitHub Pages.
- Type stubs installed with the package (autocompletion), signatures without C++ types.
