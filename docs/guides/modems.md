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

## Uncoded bit error rates

Measured by `uncoded_ber` (markers) and compared with the theory over AWGN (dotted lines):

![Uncoded BER over AWGN and Rayleigh channels](../assets/figures/modulations_ber.svg)

BPSK and QPSK have the same BER as a function of Eb/N0; the Rayleigh fading turns the exponential decrease of the
BER into a decrease in $1/(\text{Eb/N0})$.
