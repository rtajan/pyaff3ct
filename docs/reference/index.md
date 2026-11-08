# API reference

The package `aff3ct` is organized as the AFF3CT library: one sub-module per family of modules, plus the tools, the
codecs and the factories.

| Sub-module | Content |
|---|---|
| [`aff3ct.src`](modules.md#sources) | sources |
| [`aff3ct.crc`](modules.md#crcs) | CRCs |
| [`aff3ct.enc`](modules.md#encoders) | encoders |
| [`aff3ct.pct`](modules.md#puncturers) | puncturers |
| [`aff3ct.itl`](modules.md#interleavers) | interleavers |
| [`aff3ct.mdm`](modules.md#modems) | modems |
| [`aff3ct.chn`](modules.md#channels) | channels |
| [`aff3ct.qnt`](modules.md#quantizers) | quantizers |
| [`aff3ct.dec`](modules.md#decoders) | decoders |
| [`aff3ct.mnt`](modules.md#monitors) | monitors |
| [`aff3ct.cst`](modules.md#cosets), [`aff3ct.ext`](modules.md#extractors), [`aff3ct.snk`](modules.md#sinks) | cosets, extractors, sinks |
| [`aff3ct.codec`](codec.md) | codecs |
| [`aff3ct.tools`](tools.md) | tools: frozen bits, matrices, constellations, interleaver cores, noise, reporters |
| [`aff3ct.interfaces`](tools.md#interfaces) | C++ interfaces shared by several modules |
| [`aff3ct.factory`](factory.md) | AFF3CT factories |

Each module function (`af.dec.polar`...) builds its module with an AFF3CT factory: its documentation lists the
parameters of the factory and their AFF3CT default, and the arguments of the builder. In an interpreter,
`help(af.dec.polar)` shows the same text.
