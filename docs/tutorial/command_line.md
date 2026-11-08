# Factories and the AFF3CT command line

The functions of pyAFF3CT (`af.dec.polar`, `af.codec.turbo`...) hide the AFF3CT *factories*: objects that hold the
parameters of a module and build it. The factories are available in `aff3ct.factory` for two uses: reuse or
inspect a set of parameters, and configure a chain with an AFF3CT command line.

## Factories

```python
--8<-- "examples/command_line.py:factory"
```

The parameters are attributes of the factory (`f.type`, `f.L`), with the names of the AFF3CT C++ code. The arguments
of `build` are the arguments of the C++ builder (`frozen_bits`, `crc`...); the data types are keyword arguments.

## From a command line

```python
--8<-- "examples/command_line.py:from_cli"
```

`from_cli` parses the options of a factory and of its sub-factories; with `strict=False` it ignores the options of
the other factories, so that the same command line can configure the whole chain. The parameters changed after
`from_cli` are kept, and the parameters derived by AFF3CT (the BCH correction power, the size of a punctured frame...)
are derived from the command line as the simulator does.

`headers()` returns the parameters as the simulator prints them, by group:

```python
>>> import aff3ct as af
>>> f = af.factory.CRC.from_cli("--crc-poly 16-CCITT -K 32", strict=False)
>>> f.type
'16-CCITT'
```

## Keywords or command line

The same codec, with the keywords of `aff3ct.codec`:

```python
--8<-- "examples/command_line.py:keywords"
```

| Command line | Keyword |
|---|---|
| `--dec-type SCL` | `dec_type="SCL"` |
| `-L 4` (`--dec-lists`) | `dec_L=4` |
| `--enc-fb-noise 0.8` | `fbg_noise=0.8` |
| `--pct-pattern "11,10,01"` | `pct_pattern=[[1, 1], [1, 0], [0, 1]]` |

The help of a factory prints its options:

```python
--8<-- "examples/command_line.py:help"
```

The [turbo guide](../guides/turbo.md) builds the same LTE codec both ways. The test suite of pyAFF3CT rebuilds the
chains of 33 AFF3CT reference curves from their command lines.
