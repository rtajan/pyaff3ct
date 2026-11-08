# Concepts

## Modules, tasks and sockets

pyAFF3CT follows the model of StreamPU: a **module** (an encoder, a decoder...) has **tasks** (`encode`,
`decode_siho`...), and a task has **sockets**: its inputs, its outputs, and its *forward* sockets (in and out).
Each socket holds a buffer of `n_frames` frames, viewed in Python as a NumPy array:

```python
>>> import streampu as spu
>>> import aff3ct as af
>>> enc = af.enc.repetition(4, 12)
>>> u = spu.array([1, 0, 1, 1], dtype=spu.int32)
>>> x = enc.encode(u)
>>> x.numpy
array([[1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1]], dtype=int32)
>>> enc["encode::X_N"].numpy.shape
(1, 12)
```

- calling a task (`enc.encode(u)`) binds its input sockets to the sockets it receives, executes it and returns its
  output sockets (a tuple when there are several, `None` when there are none);
- `module["task::socket"]` is a socket, `module["task"]` a task;
- `module.n_frames = 8` processes 8 frames per execution (the shapes become `(8, ...)`).

## Sequences and threads

`streampu.Sequence(last_socket, n_threads=n)` analyses the graph of bindings that ends at `last_socket`, finds its
first tasks, and executes the whole graph in C++, in `n` threads. Each thread executes **clones** of the modules:

- the modules of the first thread are the original modules;
- `seq.get_cloned_modules(m)` returns the clones of `m`, one per thread;
- the clones are copies, random generators included: call `af.tools.seed_sequence(seq)` after the creation of the
  sequence, so that the sources, channels... of each thread draw their own values (otherwise every thread simulates
  the same frames with the same noise);
- a module changed after the creation of the sequence is not copied to the clones: change the clones as well, or
  create the sequence after the change;
- `af.mnt.Monitor_BFER_AR` has clones that share their counters: the sequence stops when the total reaches the
  maximum number of frame errors.

## Data types

The modules are C++ templates, instantiated for several data types:

| Parameter | Role | Values | Default |
|---|---|---|---|
| `B` | bits | `int8`, `int16`, `int32`, `int64` | `int32` |
| `R` | real values (symbols, noise) | `float32`, `float64` | `float32` |
| `Q` | LLRs of the decoders | `int8`, `int16`, `float32`, `float64` | `float32` |

They are given as keywords (`af.dec.polar(K, N, fb, B=spu.int16, Q=spu.int16)`) and the class of an object does not
depend on them: `isinstance(dec, af.dec.Decoder_SIHO)` is true whatever its types, and
`af.dec.Decoder_SIHO[spu.int16, spu.int16]` is one instantiation. See the [fixed-point guide](guides/fixed_point.md).

## Bits

In AFF3CT a bit is 0 or **non-zero**: the monitors compare booleans. The `FAST` polar decoders return a negative
value for a bit 1 (the sign bit); `af.tools.hard(x)` returns the 0 / 1 view of any array.

## Interfaces

Some features are shared by several families of modules, as C++ interfaces: the noise
(`af.interfaces.Interface_get_set_noise`), the frozen bits of the polar encoders and decoders
(`Interface_get_set_frozen_bits`), the trellis of the convolutional encoders (`Interface_get_trellis`)... The
functions of pyAFF3CT return the generic class of a module (`Decoder_SIHO`, `Encoder`...), and the methods of these
interfaces are available on the modules that implement them, checked at run time:

```python
>>> fb = af.tools.Frozenbits_generator_RM(4, 8).generate()
>>> dec = af.dec.polar(4, 8, fb, type="SC", implem="NAIVE")
>>> type(dec).__name__
'Decoder_SIHO_int32_float32'
>>> int(dec.frozen_bits.sum())
4
>>> hasattr(af.dec.repetition(4, 12), "frozen_bits")
False
```

## Noise

The noise of a simulation is a `Sigma` (Gaussian channels), an `Event_probability` (BEC, BSC) or a
`Received_optical_power`. `af.tools.sigma_from_ebn0(ebn0, code_rate, bps=1)` converts an Eb/N0 in dB:

$$\sigma = \sqrt{\frac{\text{upsample\_factor}}{2 \cdot R \cdot \text{bps} \cdot 10^{\text{Eb/N0}/10}}}$$

```python
>>> s = af.tools.sigma_from_ebn0(0.0, 0.5)
>>> round(s.sigma, 4), s.ebn0, round(s.esn0, 4)
(1.0, 0.0, -3.0103)
```
