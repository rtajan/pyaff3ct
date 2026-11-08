#!/usr/bin/env python3
"""From an AFF3CT command line to Python: factories, from_cli, headers (docs/tutorial/command_line.md).

    python examples/command_line.py
"""

from __future__ import annotations

import aff3ct as af


def run() -> dict:
    # --8<-- [start:factory]
    # every AFF3CT factory is available, with its parameters as attributes
    f = af.factory.Decoder_polar(K=32, N_cw=64, type="SCL", L=4)
    f.implem = "NAIVE"
    print(f.parameters)  # {name: value} of the parameters of the factory
    frozen_bits = af.tools.Frozenbits_generator_GA_Arikan(32, 64).generate(af.tools.Sigma(0.8))
    dec = f.build(frozen_bits)  # builder arguments as AFF3CT, dtypes by keyword: f.build(fb, B=spu.int16, Q=spu.int16)
    # --8<-- [end:factory]

    # --8<-- [start:from_cli]
    cmd = "-C POLAR -K 32 -N 64 --enc-fb-noise 0.8 --dec-type SCL --dec-implem NAIVE -L 4 --crc-poly 8-DVB-S2"
    # each factory takes its own arguments of the whole command line (strict=False: the others are ignored)
    crc_fac = af.factory.CRC.from_cli(cmd, strict=False)
    cdc_fac = af.factory.Codec_polar.from_cli(cmd, strict=False)
    crc_fac.K = 32 - 8  # the CRC is computed on the K - 8 information bits
    crc = crc_fac.build()
    cdc = cdc_fac.build(crc)
    print(cdc_fac.headers()["dec"])  # the parameters as printed by the simulator
    # --8<-- [end:from_cli]

    # --8<-- [start:keywords]
    # the same codec with the function of aff3ct.codec (prefixed parameters, as the command-line options)
    cdc2 = af.codec.polar(32, 64, crc, fbg_noise=0.8, dec_type="SCL", dec_implem="NAIVE", dec_L=4)
    # --8<-- [end:keywords]

    # --8<-- [start:help]
    af.factory.CRC().print_help()  # the command-line help of a factory
    # --8<-- [end:help]
    return {"dec": dec, "cdc": cdc, "cdc2": cdc2, "headers": cdc_fac.headers(), "parameters": f.parameters}


if __name__ == "__main__":
    run()
