# Évolution d'AFF3CT : v4.6.0-32-g8efdebe56 → v4.7.2

- Ancien : `8efdebe564` (2026-08-12)
- Nouveau : `e1b52965ae` (2026-11-03)
- **StreamPU modifié** : `b888b950a6` → `85ed022da3` — **vérifier que pystreampu épingle le même commit**
- cli inchangé : `1469711d0f`

| Niveau | Total | Sur classes `done`/`wip` (actions) |
|---|---|---|
| Changements cassants | 1 | 0 |
| Valeurs par défaut modifiées | 0 | 0 |
| Ajouts | 24 | — |
| Réorganisations sans impact attendu | 3 | — |

## Changements cassants (1) — le binding ou l'API Python doit changer

<details><summary><code>Module::Encoder_polar_PAC</code> [todo — wrap P2] — 1 changement(s)</summary>

- classes de base : `['Encoder<B>', 'tools::Interface_get_set_frozen_bits']` → `['Encoder_polar<B>']`

</details>

## Ajouts (24) — à classer et wrapper (relancer `gen_class_graph.py`)

<details><summary><code>Factory::Codec_polar_PT</code> [todo — wrap P1] — 1 changement(s)</summary>

- nouvelle classe `Factory/Tools/Codec/Polar_PT/Codec_polar_PT.hpp`  : Codec_SISO

</details>
<details><summary><code>Factory::Decoder_polar_PT</code> [todo — wrap P1] — 1 changement(s)</summary>

- nouvelle classe `Factory/Module/Decoder/Polar_PT/Decoder_polar_PT.hpp`  : Decoder

</details>
<details><summary><code>Factory::Encoder_polar</code> [todo — wrap P0] — 1 changement(s)</summary>

- paramètre/attribut ajouté : `std::string implem = "FAST"`

</details>
<details><summary><code>Factory::Encoder_polar_PT</code> [todo — wrap P1] — 1 changement(s)</summary>

- nouvelle classe `Factory/Module/Encoder/Polar_PT/Encoder_polar_PT.hpp`  : Encoder

</details>
<details><summary><code>Factory::Pretransform_generator</code> [todo — wrap P1] — 1 changement(s)</summary>

- nouvelle classe `Factory/Tools/Code/Polar_PT/Pretransform_generator.hpp`  : Factory

</details>
<details><summary><code>Module::Contents_PT_SCL</code> [todo] — 1 changement(s)</summary>

- nouvelle classe `Module/Decoder/Polar_PT/SCL/Decoder_polar_PT_SCL_naive.hpp` <typename B = int32_t, typename R = float> : —

</details>
<details><summary><code>Module::Decoder_polar_PT_SCL_naive</code> [todo — factory P2] — 1 changement(s)</summary>

- nouvelle classe `Module/Decoder/Polar_PT/SCL/Decoder_polar_PT_SCL_naive.hpp` <typename B = int, typename R = float, tools::proto_f<R>F = tools::f_LLR, tools::proto_g<B, R>G = tools::g_LLR> : Decoder_SIHO<B, R>, tools::Interface_get_set_pretransform, tools::Interface_get_set_dynamic_frozen_bits, tools::Interface_get_set_frozen_bits

</details>
<details><summary><code>Module::Encoder_polar_PT</code> [todo — wrap P2] — 1 changement(s)</summary>

- nouvelle classe `Module/Encoder/Polar_PT/Encoder_polar_PT.hpp` <typename B = int> : Encoder_polar<B>, tools::Interface_get_set_pretransform, tools::Interface_get_set_dynamic_frozen_bits

</details>
<details><summary><code>Module::Encoder_polar_bitpacked</code> [todo — wrap P2] — 1 changement(s)</summary>

- nouvelle classe `Module/Encoder/Polar/Encoder_polar_bitpacked.hpp` <typename B = int> : Encoder_polar<B>

</details>
<details><summary><code>Module::Encoder_polar_bitpacked_sys</code> [todo — wrap P2] — 1 changement(s)</summary>

- nouvelle classe `Module/Encoder/Polar/Encoder_polar_bitpacked_sys.hpp` <typename B = int> : Encoder_polar_bitpacked<B>

</details>
<details><summary><code>Module::Tree_node_info</code> [todo] — 1 changement(s)</summary>

- nouvelle classe `Module/Encoder/Polar/Encoder_polar_bitpacked.hpp`  : —

</details>
<details><summary><code>Tools::Bitonic_Merge</code> [todo — skip -] — 1 changement(s)</summary>

- nouvelle classe `Tools/Algo/Sort/Sorting_network.hpp` <int N, int DIR> : —

</details>
<details><summary><code>Tools::Bitonic_Merge_Step</code> [todo — skip -] — 1 changement(s)</summary>

- nouvelle classe `Tools/Algo/Sort/Sorting_network.hpp` <int N, int DIST, int DIR> : —

</details>
<details><summary><code>Tools::Bitonic_Sort</code> [todo — skip -] — 1 changement(s)</summary>

- nouvelle classe `Tools/Algo/Sort/Sorting_network.hpp` <int N, int DIR> : —

</details>
<details><summary><code>Tools::Codec_polar_PT</code> [todo — factory P1] — 1 changement(s)</summary>

- nouvelle classe `Tools/Codec/Polar_PT/Codec_polar_PT.hpp` <typename B = int, typename Q = float> : Codec_SISO<B, Q>, Interface_get_set_pretransform, Interface_get_set_frozen_bits, Interface_get_set_dynamic_frozen_bits

</details>
<details><summary><code>Tools::Interface_get_set_dynamic_frozen_bits</code> [done — abstract P1] — 1 changement(s)</summary>

- nouvelle classe `Tools/Interface/Interface_get_set_dynamic_frozen_bits.hpp`  : —

</details>
<details><summary><code>Tools::Interface_get_set_pretransform</code> [done — abstract P1] — 1 changement(s)</summary>

- nouvelle classe `Tools/Interface/Interface_get_set_pretransform.hpp`  : —

</details>
<details><summary><code>Tools::Merge_Prune</code> [todo — skip -] — 1 changement(s)</summary>

- nouvelle classe `Tools/Algo/Sort/Sorting_network.hpp` <int L> : —

</details>
<details><summary><code>Tools::Partial_Sort</code> [todo — skip -] — 1 changement(s)</summary>

- nouvelle classe `Tools/Algo/Sort/Sorting_network.hpp` <int N, int L> : —

</details>
<details><summary><code>Tools::Pretransform_generator</code> [todo — abstract P1] — 1 changement(s)</summary>

- nouvelle classe `Tools/Code/Polar/Pretransform_generator/Pretransform_generator.hpp`  : Interface_get_set_noise, spu::tools::Interface_clone

</details>
<details><summary><code>Tools::Pretransform_generator_file</code> [todo — wrap P1] — 1 changement(s)</summary>

- nouvelle classe `Tools/Code/Polar/Pretransform_generator/Pretransform_generator_file.hpp`  : Pretransform_generator

</details>
<details><summary><code>Tools::Sort_Blocks</code> [todo — skip -] — 1 changement(s)</summary>

- nouvelle classe `Tools/Algo/Sort/Sorting_network.hpp` <int N, int L> : —

</details>
<details><summary><code>Tools::Sorting_network</code> [todo — skip -] — 1 changement(s)</summary>

- nouvelle classe `Tools/Algo/Sort/Sorting_network.hpp` <typename T> : —

</details>
<details><summary><code>Tools::Tree_Merge_Prune</code> [todo — skip -] — 1 changement(s)</summary>

- nouvelle classe `Tools/Algo/Sort/Sorting_network.hpp` <int N_BLOCKS, int L> : —

</details>

## Réorganisations sans impact attendu (3) — vérification rapide

<details><summary><code>Module::Encoder_polar_PAC</code> [todo — wrap P2] — 3 changement(s)</summary>

- méthode `get_frozen_bits` désormais héritée de `Encoder_polar`
- méthode `light_encode` désormais héritée de `Encoder_polar`
- méthode `set_frozen_bits` désormais héritée de `Encoder_polar`

</details>

