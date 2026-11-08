# Fixed-point decoding

AFF3CT decoders exist in several precisions: the bits in `B` (`int8`, `int16`, `int32`, `int64`) and the LLRs in
`Q` (`int8`, `int16`, `float32`, `float64`). Fixed-point decoders on 8 or 16 bits process 4 or 2 times more LLRs
per SIMD instruction than on 32 bits. Script: `examples/fixed_point.py`.

## Data types

Every module function takes its data types as keywords (`B=`, `R=` for the real values, `Q=`), with the values of
`streampu`:

```python
--8<-- "examples/fixed_point.py:chain"
```

The channel and the demodulator work in floating point (`R=float32`); the **quantizer** converts the LLRs to
fixed point: they are scaled by $2^{\text{n\_decimals}}$, rounded and saturated to $\pm(2^{\text{n\_bits}-1}-1)$.
These are the AFF3CT defaults of the polar codes (`--qnt-bits 6 --qnt-dec 1`).

## Result

![Polar (128, 96), SC decoder, in 32, 16 and 8 bits](../assets/figures/fixed_point.svg)

The lines are the AFF3CT references `Polar_N128_K96_SC_NO_SYS_p{32,16,08}.txt`: 6-bit LLRs lose a few tenths of a
dB at most on this code.
