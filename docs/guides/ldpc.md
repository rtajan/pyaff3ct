# LDPC codes

Script: `examples/ldpc_matrices.py`.

## Sparse matrices

A low-density parity-check code is defined by its parity-check matrix $H$: a codeword $x$ verifies $H x = 0$ over
GF(2). `af.tools.Sparse_matrix` stores the positions of the ones:

```python
--8<-- "examples/ldpc_matrices.py:matrix"
```

## AList files

The matrices of the standards are distributed as AList files (`lib/aff3ct/conf/dec/LDPC/`):

```python
--8<-- "examples/ldpc_matrices.py:alist"
```

## Generator matrix

```python
--8<-- "examples/ldpc_matrices.py:generator"
```

`info_bits_pos` gives the positions of the information bits in the codeword: the decoder needs them to extract the
$K$ decoded bits.

## Encoder and decoder

!!! warning "Orientation"
    The LDPC modules of AFF3CT take $H$ **vertically**: $N$ rows (the variable nodes), one column per parity check.
    It is the orientation of the AList files, and `AList.read` returns the matrix as stored. A matrix written
    horizontally ($M \times N$) is turned with `H.turn(af.tools.Matrix.Way.VERTICAL)`.

```python
--8<-- "examples/ldpc_matrices.py:modules"
```

Decoder types (`--dec-type`): `BP_FLOODING`, `BP_HORIZONTAL_LAYERED`, `BP_VERTICAL_LAYERED`, `BIT_FLIPPING`,
`BP_PEELING`; implementations (`--dec-implem`) of the check nodes: `SPA` (sum-product), `LSPA`, `MS` (min-sum),
`OMS` (offset min-sum), `NMS` (normalized min-sum), `AMS`...

## With a codec

The codec reads the matrix from its file and computes the encoder:

```python
--8<-- "examples/codecs_comparison.py:ldpc"
```

A full simulation is in `examples/ldpc_bfer.py`:

```python
--8<-- "examples/ldpc_bfer.py:codec"
```
