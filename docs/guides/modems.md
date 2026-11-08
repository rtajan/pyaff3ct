# Modulations and channels

Script: `examples/modulations.py`.

## Modems

`af.mdm.modem` builds the modems of AFF3CT (`--mdm-type`): `BPSK`, `OOK`, `PAM`, `PSK`, `QAM`, `CPM`, `SCMA`, and
generic modems for any constellation. A modem modulates bits into symbols and demodulates the received symbols into
log-likelihood ratios (LLRs).

```python
--8<-- "examples/modulations.py:modems"
```

- `bps` is the number of bits per symbol;
- `symbols=` builds a modem for any list of $2^{bps}$ complex symbols (normalized to a unit mean energy);
- the demodulator computes exact LLRs, or max-log LLRs with `max="MAX"` (`--mdm-max`).

### Constellations and bit labels

```python
--8<-- "examples/modulations.py:constellation"
```

The symbol $i$ carries the bits of the integer $i$, **least significant bit first**: with 16-QAM, the bits
`1, 0, 0, 0` are mapped to the symbol 1. The PAM, PSK and QAM constellations of AFF3CT are Gray-mapped.

A user constellation can be labelled the other way, the first bit being the **most** significant one:

```python
>>> import aff3ct as af
>>> mdm = af.mdm.modem(4, symbols=[-3, -1, 3, 1], bit_order="MSB")   # Gray-mapped 4-PAM: 00, 01, 11, 10
>>> import streampu as spu
>>> x = mdm.modulate(spu.array([1, 1, 1, 0], dtype=spu.int32))       # bits 1, 1 then 1, 0
>>> [round(float(v) * 5 ** 0.5, 3) for v in x.numpy[0, 0::2]]         # real parts (unit mean energy: / sqrt(5))
[1.0, 3.0]
```

![16-QAM constellation](../assets/figures/qam16.svg){ width="420" }

## Channels

```python
--8<-- "examples/modulations.py:channels"
```

`af.chn.channel` builds the channels of AFF3CT (`--chn-type`): `NO`, `AWGN`, `RAYLEIGH`, `RAYLEIGH_USER`, `BEC`,
`BSC`, `OPTICAL`, `USER`... Its size is the size of the **modulated** frame, `mdm.N_mod`: for complex symbols, the
real and imaginary parts are interleaved, and the channel is built with `complex=True`.

!!! warning "Eb/N0 and bits per symbol"
    The noise variance depends on the number of bits per symbol: give it to the conversion,
    `af.tools.sigma_from_ebn0(ebn0, code_rate, bps=bps)`.

### Fading channels

The Rayleigh channel multiplies each symbol by a random gain $h$. Its task `add_noise_wg` (*with gains*) also
outputs the gains, that the demodulator uses through `demodulate_wg`:

```python
--8<-- "examples/modulations.py:uncoded"
```

## SCMA and CPM

Script: `examples/scma_cpm.py`; the test suite compares both with the AFF3CT references.

### SCMA

Sparse code multiple access multiplexes 6 users on 4 resources: the modem works on the frames of the 6 users at
once (`mdm.n_frames == 6`), every module of the chain must do the same, and the channel sums the signals of the users
(`add_users=True`). The codebooks are read from the AFF3CT configuration files (`conf/mod/SCMA`):

```python
--8<-- "examples/scma_cpm.py:scma"
```

### CPM

Continuous phase modulations (`cpm_k / cpm_p` modulation index, memory `cpm_L`, pulse `cpm_wave_shape`, or a standard
such as `cpm_std="GSM"`) oversample the signal (`cpm_upf` samples per symbol, to give to the Eb/N0 conversion) and
filter the received signal before the demodulation:

```python
--8<-- "examples/scma_cpm.py:cpm"
```

## Uncoded bit error rates

Measured by `uncoded_ber` (markers) and compared with the theory over AWGN (dotted lines):

![Uncoded BER over AWGN and Rayleigh channels](../assets/figures/modulations_ber.svg)

BPSK and QPSK have the same BER as a function of Eb/N0; the Rayleigh fading turns the exponential decrease of the
BER into a decrease in $1/(\text{Eb/N0})$.
