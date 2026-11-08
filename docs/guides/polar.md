# Polar codes

Script: `examples/polar_codes.py`.

## Frozen bits

A polar code of size $N = 2^n$ transmits its $K$ information bits on the $K$ most reliable *bit channels*; the
$N - K$ others are *frozen* (set to 0). Their positions are given to the encoder and to the decoder as a boolean
array, computed by a frozen bits generator:

```python
--8<-- "examples/polar_codes.py:frozen_bits"
```

| Generator | Construction |
|---|---|
| `Frozenbits_generator_GA_Arikan` | Gaussian approximation, depends on the noise |
| `Frozenbits_generator_GA` | Gaussian approximation (Trifonov, multi-kernel codes), depends on the noise |
| `Frozenbits_generator_TV` | Tal & Vardy, depends on the noise |
| `Frozenbits_generator_BEC` | erasure channel, depends on the erasure probability |
| `Frozenbits_generator_RM` | Reed-Muller (weight of the rows), independent of the noise |
| `Frozenbits_generator_5G` | reliability sequence of the 5G standard |
| `Frozenbits_generator_file` | read from a file (AFF3CT format) |

## Decoders

```python
--8<-- "examples/polar_codes.py:decoders"
```

The `type` of the decoder is the AFF3CT `--dec-type`: `SC` (successive cancellation), `SCL` (list), `SCL_MEM`,
`ASCL` (adaptive list), `SCAN` (soft output), `BP_FLOODING`, `BP_PEELING`...; `implem` is `NAIVE` or `FAST`
(SIMD, with tree pruning).

!!! note "Hard outputs of the `FAST` decoders"
    The `FAST` decoders return 0 for a bit 0 and **a non-zero value** for a bit 1 (`-128` in `int8`...), as AFF3CT
    does: its monitors only compare the bits with zero. `af.tools.hard(v)` gives the 0 / 1 view.

### CRC-aided list decoding

```python
--8<-- "examples/polar_codes.py:ca_scl"
```

The CRC is computed on the first $K - |\text{CRC}|$ bits: the source generates `crc.K` bits, `crc.build(u)` appends
the CRC, and `crc.extract(v)` removes it after decoding (see `simulate` in the [codecs tutorial](../tutorial/codecs.md#using-a-codec)).

## Frozen bits and threads

When the frozen bits depend on the noise, they must change at each Eb/N0. A `Sequence` holds **copies** of the
modules (one per thread), made when it is created:

```python
--8<-- "examples/polar_codes.py:clones"
```

The [BER/FER tutorial](../tutorial/bfer.md#the-snr-loop) shows the other way: keep the sequence and call
`set_frozen_bits` on `seq.get_cloned_modules(enc)` and `seq.get_cloned_modules(dec)`.

## Variants

Script: `examples/polar_variants.py`. The kernels, frozen bits and pre-transforms come from the configuration files of
AFF3CT (`lib/aff3ct/conf`, fetched by `scripts/fetch_aff3ct_data.sh`).

### Multi-kernel polar codes

The polar transform is a product of kernels of several sizes ($2 \times 2$, $3 \times 3$...), which gives code lengths
that are not powers of 2. The kernels and their order are read from a code file (`pc_code_path`, the AFF3CT option
`--enc-pc-path`):

```python
--8<-- "examples/polar_variants.py:mk"
```

### PAC codes

Polarization-adjusted convolutional codes encode the information bits with a convolutional code before the polar
transform (`enc_conv`, octal polynomial, `--enc-conv`); the decoder is a list (`SCL`) or a Fano (`FANO`) decoder:

```python
--8<-- "examples/polar_variants.py:pac"
```

### Pre-transformed polar codes

A binary pre-transform matrix is applied before the polar transform, its frozen bits and matrix read from files
(`ptg_*`, `--enc-pt-*`):

```python
--8<-- "examples/polar_variants.py:pt"
```

The three codecs are used as the other ones (`cdc.encoder`, `cdc.decoder_siho`); the test suite rebuilds 8 reference
curves of these families from their AFF3CT command lines.
