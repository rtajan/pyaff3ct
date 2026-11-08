# Codecs

A *codec* builds and connects all the modules of a code family: the encoder, the decoders, the puncturer, the
interleaver... with the parameters of the AFF3CT command line. It is the easiest way to use a code: one function
per family in `aff3ct.codec`.

| Function | Code | | Function | Code |
|---|---|---|---|---|
| `polar` | polar (Arikan kernel) | | `turbo` | turbo (parallel concatenation of RSC) |
| `polar_mk` | polar, multi-kernel | | `turbo_db` | double-binary turbo |
| `polar_pac` | PAC (polarization-adjusted convolutional) | | `turbo_product` | turbo product (BCH) |
| `ldpc` | LDPC | | `rsc`, `rsc_db` | recursive systematic convolutional |
| `bch` | BCH | | `ra` | repeat-accumulate |
| `rs` | Reed-Solomon | | `repetition`, `uncoded` | repetition, no code |

## Parameters

The positional parameters are those of the codec (`K`, `N_cw`, the CRC); the parameters of the sub-factories are
**prefixed** as the command-line options: `--dec-type` becomes `dec_type`, `--enc-sub-std` becomes
`enc_sub_standard`, `--pct-pattern` becomes `pct_pattern`:

```python
--8<-- "examples/codecs_comparison.py:codecs"
```

`N` is the frame size after puncturing: when it differs from `N_cw`, the codec adds a puncturer. The LDPC codes
read their parity-check matrix from a file:

```python
--8<-- "examples/codecs_comparison.py:ldpc"
```

`help(af.codec.turbo)` lists every parameter, with its AFF3CT default.

## Using a codec

The modules of the codec are its attributes: `cdc.encoder`, `cdc.decoder_siho` (soft input, hard output),
`cdc.decoder_siso` when the code has one, `cdc.puncturer`, `cdc.interleaver`. The same function then simulates every
code:

```python
--8<-- "examples/codecs_comparison.py:simulate"
```

!!! warning "Polar codes: `set_noise` before the Sequence"
    `cdc.set_noise(noise)` computes the frozen bits for this noise (unless they are fixed by `fbg_noise`) and gives
    them to the encoder and the decoders of the codec. A `Sequence` copies the modules when it is created: create it
    after `set_noise`, or update its clones (see the [polar guide](../guides/polar.md#frozen-bits-and-threads)).

## Comparison

Codes of 64 information bits and rate 1/2, BPSK over AWGN (`python examples/codecs_comparison.py --plot`):

![FER of codes of rate 1/2](../assets/figures/codecs_comparison.svg)

At this short length, the CRC-aided list decoding of the polar code is the best; the turbo code would win at larger
sizes ([turbo guide](../guides/turbo.md)).
