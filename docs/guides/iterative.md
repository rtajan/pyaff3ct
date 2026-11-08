# Iterative receivers

Script: `examples/turbo_demodulation.py`; the test suite compares it, and the same chain built from the command
lines of the AFF3CT references (`--sim-type BFERI`), with the AFF3CT references.

In an iterative receiver, two soft-input soft-output blocks exchange information several times on the same frame.
With a modulation that has memory (CPM, here the GMSK of the GSM standard), the demodulator and the decoder do a
*turbo demodulation*: the decoder extrinsic information becomes the a priori information of the demodulator
(`tdemodulate`), whose output goes back to the decoder. This is the `BFERI` simulation of AFF3CT.

## The modules

The loop is made of two StreamPU modules: a `Switcher` with two paths (`0`: one more iteration, `1`: end of the
loop) and an `Iterator`, which gives path `0` `n_ite` times, then path `1`. The interleavers share one interleaver
core: the same permutation for the bits sent and for the LLRs in both directions. Two modems: one for the first
demodulation, one for the demodulations with a priori information in the loop.

```python
--8<-- "examples/turbo_demodulation.py:modules"
```

## The loop

The loop cannot be executed before it is closed: the bindings are made with `spu.Task.call_auto_exec = False`
(the tasks are bound, not executed). `select` opens the loop (first time: the LLRs of the channel, then the output of
the previous iteration) and `commute` chooses between one more iteration and the end; `iterate` is bound to
`select`, so that it counts the passes through the loop.

```python
--8<-- "examples/turbo_demodulation.py:loop"
```

```text
 channel LLRs ──► select ──► commute ─0─► decode_siso ──► interleave ──► tdemodulate ──► deinterleave ─┐
                    ▲           │                                                                     │
                    └───────────┼─────────────────────────────────────────────────────────────────────┘
                                └─1─► decode_siho ──► check_errors
```

## Running it

```python
--8<-- "examples/turbo_demodulation.py:run"
```

`af.tools.reset_decoders_on_check(seq)` matters: some SISO decoders keep information from one call to the next on
the same frame (the LDPC BP decoders keep their messages). By default a decoder starts each call from a blank
state; this function keeps the state across the iterations of a frame and resets it once the monitor of its
thread has checked the frame, as the AFF3CT simulator. Without it, the iterations bring much less (here, at 1.75 dB,
a frame error rate close to 1 instead of 0.3 after 10 iterations).

!!! note "One sequence"
    The monitors then hold the callbacks of the decoders, and AFF3CT does not clone a monitor with callbacks: keep
    one sequence and change its inputs (the noise) between the executions, or call `mnt.clear_callbacks()` before
    building another sequence with the same modules.

| Eb/N0 (dB) | iterations | FER (pyaff3ct, 50 errors) | FER (AFF3CT reference) |
|-----------:|-----------:|--------------------------:|-----------------------:|
| 1.50       | 10         | 0.79                      | 0.83                   |
| 1.75       | 1          | 1.00                      |                        |
| 1.75       | 10         | 0.32                      | 0.29                   |

## Coset approach

The AFF3CT references use the *coset approach* (`--sim-coset`): random codewords (`COSET` encoder, no generator
matrix needed) and `af.cst.coset_real` / `af.cst.coset_bit` modules around the decoder, which then sees the
all-zero codeword. `run_bferi_reference` in `tests/test_references.py` builds this variant from the command lines.
