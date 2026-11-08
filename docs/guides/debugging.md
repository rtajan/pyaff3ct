# Debugging

Script: `examples/debugging.py`.

## Text view of frames

`af.tools.Frame_trace` formats frames of bits, reals or hexadecimal values, compared with a reference (the bits
sent): it returns the text, to print.

```python
--8<-- "examples/debugging.py:trace"
```

## Recording the frames in error

`af.tools.Dumper` copies registered sockets each time `add(n_errors, frame_id)` is called with more errors than a
threshold (`add_threshold`), typically from the callback of a BFER monitor, then writes one file per socket
(`n_frames frame_size`, then the frames). Replayed through a `USER` source and channel, they reproduce the errors.

```python
--8<-- "examples/debugging.py:dumper"
```

!!! warning "One thread"
    The callbacks of a monitor are called in the threads of the sequence: with a Python callback, run the sequence
    on one thread.

## Histograms

`af.tools.Histogram` counts real values rounded to `precision` decimals; `Monitor_MI` records the mutual information
of each frame in one (`activate_mutinfo_histogram(True)`, then `mnt.mutinfo_hist`).

```python
--8<-- "examples/debugging.py:histogram"
```
