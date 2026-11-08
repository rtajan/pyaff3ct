# Turbo codes

Script: `examples/turbo_lte.py`. This page reproduces the AFF3CT reference
`refs/TURBO/AWGN/BPSK/RSC_RSC/BCJR/LTE/Turbo_N4096_K2048_BCJR_i8_ref_LTE.txt`: the LTE turbo code, $K = 2048$,
a 24-bit CRC, punctured to rate 1/2, 8 iterations of a max-log-MAP BCJR decoder.

```mermaid
flowchart LR
    u[U] --> crc[CRC<br>build] --> enc
    subgraph enc [turbo encoder]
        direction TB
        rsc1[RSC 1]
        itl[interleaver] --> rsc2[RSC 2]
    end
    enc -- "N_cw = 3K + 12" --> pct[puncturer<br>puncture] -- N --> chn[BPSK + AWGN] --> dpct[puncturer<br>depuncture] -- N_cw --> dec[turbo decoder<br>BCJR x 2, 8 it.] --> ext[CRC<br>extract]
```

## From keywords

```python
--8<-- "examples/turbo_lte.py:keywords"
```

## From the AFF3CT command line

```python
--8<-- "examples/turbo_lte.py:command_line"
```

with

```python
--8<-- "examples/turbo_lte.py:command"
```

## The chain

```python
--8<-- "examples/turbo_lte.py:chain"
```

The decoder stops its iterations when the CRC is verified, which saves most of them at high SNR.

![LTE turbo code, K = 2048, rate 1/2](../assets/figures/turbo_lte.svg)

## Other turbo codes

- `af.codec.turbo_db`: double-binary turbo codes (DVB-RCS1, DVB-RCS2), `enc_sub_standard="DVB-RCS1"`;
- `af.codec.turbo_product`: product of two BCH codes, Chase-Pyndiah decoder;
- the interleaver is chosen with `itl_core_type` (`LTE`, `CCSDS`, `DVB-RCS1`, `RANDOM`, `ROW_COL`...).
