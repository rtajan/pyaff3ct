# Simulating BER / FER curves

A BER/FER curve repeats the [first chain](first_chain.md) for several values of Eb/N0. This page reproduces the
AFF3CT command

```bash
aff3ct --sim-type BFER -C POLAR -K 96 -N 128 --enc-fb-gen-method GA --enc-no-sys --dec-type SC --dec-implem NAIVE
```

with a few lines of Python, on several threads, and with the same terminal output as the simulator. The full script
is `examples/polar_bfer.py`:

```bash
python examples/polar_bfer.py --ebn0 0 4 0.5 --max-fe 100 --threads 4 --plot polar.svg
```

## The chain

```python
--8<-- "examples/polar_bfer.py:chain"
```

`Monitor_BFER_AR` is the monitor of the multi-threaded simulations: every thread runs a clone of the chain, and the
clones of the monitor share their counters. The sequence stops when the **total** of the frame errors reaches
`max_fe`, and `mnt.fer` shows the total.

## The SNR loop

```python
--8<-- "examples/polar_bfer.py:simulate"
```

- `spu.Sequence(..., n_threads=n_threads)` clones the modules once per thread. The modules of the first thread are
  the original ones; `seq.get_cloned_modules(m)` returns the clones of `m` in all the threads, to update the
  frozen bits of every encoder and decoder.
- `af.tools.seed_sequence(seq)` gives each thread its own seeds: the clones are copies, random generators
  included, and without it every thread would draw the same frames and the same noise (as many threads, no more
  information than one). The AFF3CT simulator does the same.
- `spu.Terminal_std` prints the reports of the reporters (noise, BER/FER, throughput) as the AFF3CT simulator does.
- the `sigma` socket is changed in place: the bindings of the sequence are kept.

## Result

The points are the output of `simulate`, the lines are the AFF3CT reference curve
(`refs/POLAR/AWGN/BPSK/SC/Polar_N128_K96_SC_NO_SYS_p32.txt`):

![Polar (128, 96), SC decoder: pyAFF3CT and AFF3CT](../assets/figures/polar_bfer.svg)

!!! tip "Statistical precision"
    With `max_fe` frame errors, the relative standard deviation of the FER is about $1/\sqrt{\text{max\_fe}}$:
    10 % for 100 errors. The tests compare the examples with the references within 4 standard deviations.
