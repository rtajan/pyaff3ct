# Monitors

A monitor is the last module of a chain: it measures, and its `is_done()` stops the `streampu.Sequence`.

| Function | Class | Task | Measures |
|---|---|---|---|
| `af.mnt.bfer(K, n_frame_errors=...)` | `Monitor_BFER` | `check_errors(U, V)` | `n_fe`, `n_be`, `fer`, `ber`, `n_analyzed_frames` |
| `af.mnt.Monitor_BFER_AR(K, max_fe)` | `Monitor_BFER_AR` | `check_errors(U, V)` | same, totals of all the threads |
| `af.mnt.mi(N, n_trials=...)` | `Monitor_MI` | `get_mutual_info(X, Y)` | `mi`, `mi_min`, `mi_max`, `n_trials` |
| `af.mnt.exit(size, n_trials=...)` | `Monitor_EXIT` | `check_mutual_info(bits, llrs_a, llrs_e)` | `I_A`, `I_E`, `n_trials` |

## Threads: `af.mnt.reduce`

In a sequence on several threads, each thread runs a clone of the monitor and measures its own frames
(`Monitor_BFER_AR` excepted: its clones share their counters, and the sequence stops on the total).
`af.mnt.reduce(seq, mnt)` returns a new monitor with the measures of all the threads, the role of
`Monitor_reduction` in the AFF3CT simulator.

## Mutual information

The mutual information between bits and their LLRs, frame by frame. Script: `examples/mutual_information.py`, which
measures the capacity of the binary input AWGN channel with the LLRs of a BPSK demodulator:

```python
--8<-- "examples/mutual_information.py:mi"
```

![Mutual information of the LLRs of a BPSK demodulator over AWGN: the BI-AWGN capacity](../assets/figures/capacity.svg)

!!! note "Frame size"
    The monitor estimates the mutual information of each frame, then averages: on short frames the estimate is
    biased upwards (about +0.008 bit at Es/N0 = -10 dB with 1024 bits, +0.002 with 16384 bits).

## EXIT charts

`Monitor_EXIT` measures the two coordinates of a point of the EXIT chart of a soft-input soft-output decoder: the
mutual information of the a priori LLRs given to the decoder (`I_A`) and of the extrinsic LLRs it returns (`I_E`).

## Reporters

`af.tools.Reporter_BFER(mnt)`, `Reporter_MI(mnt)` and `Reporter_EXIT(mnt, noise_a)` give the columns of these
monitors to `streampu.Terminal_std`, as the AFF3CT simulator prints them (see the
[BER/FER tutorial](../tutorial/bfer.md#the-snr-loop)).
