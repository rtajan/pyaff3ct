# Représentation des bits dans AFF3CT

> Généré par `scripts/probe_bit_convention.py` (AFF3CT v4.7.2) — ne pas éditer à la main.

Dans AFF3CT, un bit vaut 0 ou **non nul** : les moniteurs comparent des booléens (`Boolean_diff`). Certains modules rendent donc autre chose que 1 pour un 1 ; `aff3ct.tools.hard(x)` donne la vue 0 / 1. Chaque ligne est mesurée sur une trame sans bruit : valeurs distinctes des sorties, ⚠ quand elles ne sont pas 0 / 1, et décodage correct (en booléens).

**24 combinaison(s) sur 100 rendent autre chose que 0 / 1 :**

- `af.dec.polar` type `SC`, implem `FAST`, (int8, int8)
- `af.dec.polar` type `SC`, implem `FAST`, (int16, int16)
- `af.dec.polar` type `SC`, implem `FAST`, (int32, float32)
- `af.dec.polar` type `SC`, implem `FAST`, (int64, float64)
- `af.dec.polar` type `SCL`, implem `FAST`, (int8, int8)
- `af.dec.polar` type `SCL`, implem `FAST`, (int16, int16)
- `af.dec.polar` type `SCL`, implem `FAST`, (int32, float32)
- `af.dec.polar` type `SCL`, implem `FAST`, (int64, float64)
- `af.dec.polar` type `SCL_MEM`, implem `FAST`, (int8, int8)
- `af.dec.polar` type `SCL_MEM`, implem `FAST`, (int16, int16)
- `af.dec.polar` type `SCL_MEM`, implem `FAST`, (int32, float32)
- `af.dec.polar` type `SCL_MEM`, implem `FAST`, (int64, float64)
- `af.dec.polar` type `ASCL`, implem `FAST`, (int8, int8)
- `af.dec.polar` type `ASCL`, implem `FAST`, (int16, int16)
- `af.dec.polar` type `ASCL`, implem `FAST`, (int32, float32)
- `af.dec.polar` type `ASCL`, implem `FAST`, (int64, float64)
- `af.dec.polar` type `ASCL_MEM`, implem `FAST`, (int8, int8)
- `af.dec.polar` type `ASCL_MEM`, implem `FAST`, (int16, int16)
- `af.dec.polar` type `ASCL_MEM`, implem `FAST`, (int32, float32)
- `af.dec.polar` type `ASCL_MEM`, implem `FAST`, (int64, float64)
- `af.dec.polar` type `SCAN`, implem `NAIVE`, (int8, int8)
- `af.dec.polar` type `SCAN`, implem `NAIVE`, (int16, int16)
- `af.dec.polar` type `SCAN`, implem `NAIVE`, (int32, float32)
- `af.dec.polar` type `SCAN`, implem `NAIVE`, (int64, float64)

Non couverts pour l'instant (outils ou classes concrètes pas encore wrappés) : LDPC (`Sparse_matrix`), BCH / RS (générateur `GF`), RSC / conv. (`trellis` de l'encodeur concret), RA / turbo / turbo produit (`Interleaver_core`), polaire MK / PAC / PT (`Polar_code`, pré-transformation).

| Fonction | Type | Implem | (B, Q) | `encode::X_N` | `decode_siho::V_K` | `decode_siho_cw::V_N` | Décodage |
|---|---|---|---|---|---|---|---|
| `polar` | `SC` | `FAST` | (int8, int8) | 0, 1 | -128, 0 ⚠ | -128, 0 ⚠ | ✓ |
| `polar` | `SC` | `FAST` | (int16, int16) | 0, 1 | -32768, 0 ⚠ | -32768, 0 ⚠ | ✓ |
| `polar` | `SC` | `FAST` | (int32, float32) | 0, 1 | -2147483648, 0 ⚠ | -2147483648, 0 ⚠ | ✓ |
| `polar` | `SC` | `FAST` | (int64, float64) | 0, 1 | -9223372036854775808, 0 ⚠ | -9223372036854775808, 0 ⚠ | ✓ |
| `polar` | `SC` | `NAIVE` | (int8, int8) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `polar` | `SC` | `NAIVE` | (int16, int16) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `polar` | `SC` | `NAIVE` | (int32, float32) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `polar` | `SC` | `NAIVE` | (int64, float64) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `polar` | `SCL` | `FAST` | (int8, int8) | 0, 1 | -128, 0 ⚠ | -128, 0 ⚠ | ✓ |
| `polar` | `SCL` | `FAST` | (int16, int16) | 0, 1 | -32768, 0 ⚠ | -32768, 0 ⚠ | ✓ |
| `polar` | `SCL` | `FAST` | (int32, float32) | 0, 1 | -2147483648, 0 ⚠ | -2147483648, 0 ⚠ | ✓ |
| `polar` | `SCL` | `FAST` | (int64, float64) | 0, 1 | -9223372036854775808, 0 ⚠ | -9223372036854775808, 0 ⚠ | ✓ |
| `polar` | `SCL` | `NAIVE` | (int8, int8) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `polar` | `SCL` | `NAIVE` | (int16, int16) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `polar` | `SCL` | `NAIVE` | (int32, float32) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `polar` | `SCL` | `NAIVE` | (int64, float64) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `polar` | `SCL_MEM` | `FAST` | (int8, int8) | 0, 1 | -128, 0 ⚠ | -128, 0 ⚠ | ✓ |
| `polar` | `SCL_MEM` | `FAST` | (int16, int16) | 0, 1 | -32768, 0 ⚠ | -32768, 0 ⚠ | ✓ |
| `polar` | `SCL_MEM` | `FAST` | (int32, float32) | 0, 1 | -2147483648, 0 ⚠ | -2147483648, 0 ⚠ | ✓ |
| `polar` | `SCL_MEM` | `FAST` | (int64, float64) | 0, 1 | -9223372036854775808, 0 ⚠ | -9223372036854775808, 0 ⚠ | ✓ |
| `polar` | `SCL_MEM` | `NAIVE` | (int8, int8) |  |  |  | non construit (CannotAllocate: _build: "Cannot allocate the object.":) |
| `polar` | `SCL_MEM` | `NAIVE` | (int16, int16) |  |  |  | non construit (CannotAllocate: _build: "Cannot allocate the object.":) |
| `polar` | `SCL_MEM` | `NAIVE` | (int32, float32) |  |  |  | non construit (CannotAllocate: _build: "Cannot allocate the object.":) |
| `polar` | `SCL_MEM` | `NAIVE` | (int64, float64) |  |  |  | non construit (CannotAllocate: _build: "Cannot allocate the object.":) |
| `polar` | `ASCL` | `FAST` | (int8, int8) | 0, 1 | -128, 0 ⚠ | -128, 0 ⚠ | ✓ |
| `polar` | `ASCL` | `FAST` | (int16, int16) | 0, 1 | -32768, 0 ⚠ | -32768, 0 ⚠ | ✓ |
| `polar` | `ASCL` | `FAST` | (int32, float32) | 0, 1 | -2147483648, 0 ⚠ | -2147483648, 0 ⚠ | ✓ |
| `polar` | `ASCL` | `FAST` | (int64, float64) | 0, 1 | -9223372036854775808, 0 ⚠ | -9223372036854775808, 0 ⚠ | ✓ |
| `polar` | `ASCL` | `NAIVE` | (int8, int8) |  |  |  | non construit (CannotAllocate: _build: "Cannot allocate the object.":) |
| `polar` | `ASCL` | `NAIVE` | (int16, int16) |  |  |  | non construit (CannotAllocate: _build: "Cannot allocate the object.":) |
| `polar` | `ASCL` | `NAIVE` | (int32, float32) |  |  |  | non construit (CannotAllocate: _build: "Cannot allocate the object.":) |
| `polar` | `ASCL` | `NAIVE` | (int64, float64) |  |  |  | non construit (CannotAllocate: _build: "Cannot allocate the object.":) |
| `polar` | `ASCL_MEM` | `FAST` | (int8, int8) | 0, 1 | -128, 0 ⚠ | -128, 0 ⚠ | ✓ |
| `polar` | `ASCL_MEM` | `FAST` | (int16, int16) | 0, 1 | -32768, 0 ⚠ | -32768, 0 ⚠ | ✓ |
| `polar` | `ASCL_MEM` | `FAST` | (int32, float32) | 0, 1 | -2147483648, 0 ⚠ | -2147483648, 0 ⚠ | ✓ |
| `polar` | `ASCL_MEM` | `FAST` | (int64, float64) | 0, 1 | -9223372036854775808, 0 ⚠ | -9223372036854775808, 0 ⚠ | ✓ |
| `polar` | `ASCL_MEM` | `NAIVE` | (int8, int8) |  |  |  | non construit (CannotAllocate: _build: "Cannot allocate the object.":) |
| `polar` | `ASCL_MEM` | `NAIVE` | (int16, int16) |  |  |  | non construit (CannotAllocate: _build: "Cannot allocate the object.":) |
| `polar` | `ASCL_MEM` | `NAIVE` | (int32, float32) |  |  |  | non construit (CannotAllocate: _build: "Cannot allocate the object.":) |
| `polar` | `ASCL_MEM` | `NAIVE` | (int64, float64) |  |  |  | non construit (CannotAllocate: _build: "Cannot allocate the object.":) |
| `polar` | `SCAN` | `FAST` | (int8, int8) |  |  |  | non construit (CannotAllocate: _build: "Cannot allocate the object.":) |
| `polar` | `SCAN` | `FAST` | (int16, int16) |  |  |  | non construit (CannotAllocate: _build: "Cannot allocate the object.":) |
| `polar` | `SCAN` | `FAST` | (int32, float32) |  |  |  | non construit (CannotAllocate: _build: "Cannot allocate the object.":) |
| `polar` | `SCAN` | `FAST` | (int64, float64) |  |  |  | non construit (CannotAllocate: _build: "Cannot allocate the object.":) |
| `polar` | `SCAN` | `NAIVE` | (int8, int8) | 0, 1 | -128, 0 ⚠ | -128, 0 ⚠ | ✓ |
| `polar` | `SCAN` | `NAIVE` | (int16, int16) | 0, 1 | -32768, 0 ⚠ | -32768, 0 ⚠ | ✓ |
| `polar` | `SCAN` | `NAIVE` | (int32, float32) | 0, 1 | -2147483648, 0 ⚠ | -2147483648, 0 ⚠ | ✓ |
| `polar` | `SCAN` | `NAIVE` | (int64, float64) | 0, 1 | -9223372036854775808, 0 ⚠ | -9223372036854775808, 0 ⚠ | ✓ |
| `polar` | `SCF` | `FAST` | (int8, int8) |  |  |  | non construit (CannotAllocate: _build: "Cannot allocate the object.":) |
| `polar` | `SCF` | `FAST` | (int16, int16) |  |  |  | non construit (CannotAllocate: _build: "Cannot allocate the object.":) |
| `polar` | `SCF` | `FAST` | (int32, float32) |  |  |  | non construit (CannotAllocate: _build: "Cannot allocate the object.":) |
| `polar` | `SCF` | `FAST` | (int64, float64) |  |  |  | non construit (CannotAllocate: _build: "Cannot allocate the object.":) |
| `polar` | `SCF` | `NAIVE` | (int8, int8) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `polar` | `SCF` | `NAIVE` | (int16, int16) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `polar` | `SCF` | `NAIVE` | (int32, float32) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `polar` | `SCF` | `NAIVE` | (int64, float64) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `polar` | `ML` | `STD` | (int8, int8) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `polar` | `ML` | `STD` | (int16, int16) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `polar` | `ML` | `STD` | (int32, float32) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `polar` | `ML` | `STD` | (int64, float64) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `polar` | `CHASE` | `STD` | (int8, int8) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `polar` | `CHASE` | `STD` | (int16, int16) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `polar` | `CHASE` | `STD` | (int32, float32) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `polar` | `CHASE` | `STD` | (int64, float64) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `repetition` | `REPETITION` | `STD` | (int8, int8) | 0, 1 | 0, 1 | — | ✓ |
| `repetition` | `REPETITION` | `STD` | (int16, int16) | 0, 1 | 0, 1 | — | ✓ |
| `repetition` | `REPETITION` | `STD` | (int32, float32) | 0, 1 | 0, 1 | — | ✓ |
| `repetition` | `REPETITION` | `STD` | (int64, float64) | 0, 1 | 0, 1 | — | ✓ |
| `repetition` | `REPETITION` | `FAST` | (int8, int8) | 0, 1 | 0, 1 | — | ✓ |
| `repetition` | `REPETITION` | `FAST` | (int16, int16) | 0, 1 | 0, 1 | — | ✓ |
| `repetition` | `REPETITION` | `FAST` | (int32, float32) | 0, 1 | 0, 1 | — | ✓ |
| `repetition` | `REPETITION` | `FAST` | (int64, float64) | 0, 1 | 0, 1 | — | ✓ |
| `repetition` | `REPETITION_VOTE` | `STD` | (int8, int8) | 0, 1 | 0, 1 | — | ✓ |
| `repetition` | `REPETITION_VOTE` | `STD` | (int16, int16) | 0, 1 | 0, 1 | — | ✓ |
| `repetition` | `REPETITION_VOTE` | `STD` | (int32, float32) | 0, 1 | 0, 1 | — | ✓ |
| `repetition` | `REPETITION_VOTE` | `STD` | (int64, float64) | 0, 1 | 0, 1 | — | ✓ |
| `repetition` | `REPETITION_VOTE` | `FAST` | (int8, int8) |  |  |  | non construit (CannotAllocate: build: "Cannot allocate the object.":) |
| `repetition` | `REPETITION_VOTE` | `FAST` | (int16, int16) |  |  |  | non construit (CannotAllocate: build: "Cannot allocate the object.":) |
| `repetition` | `REPETITION_VOTE` | `FAST` | (int32, float32) |  |  |  | non construit (CannotAllocate: build: "Cannot allocate the object.":) |
| `repetition` | `REPETITION_VOTE` | `FAST` | (int64, float64) |  |  |  | non construit (CannotAllocate: build: "Cannot allocate the object.":) |
| `repetition` | `ML` | `STD` | (int8, int8) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `repetition` | `ML` | `STD` | (int16, int16) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `repetition` | `ML` | `STD` | (int32, float32) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `repetition` | `ML` | `STD` | (int64, float64) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `repetition` | `CHASE` | `STD` | (int8, int8) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `repetition` | `CHASE` | `STD` | (int16, int16) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `repetition` | `CHASE` | `STD` | (int32, float32) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `repetition` | `CHASE` | `STD` | (int64, float64) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `no` | `NONE` | `HARD_DECISION` | (int8, int8) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `no` | `NONE` | `HARD_DECISION` | (int16, int16) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `no` | `NONE` | `HARD_DECISION` | (int32, float32) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `no` | `NONE` | `HARD_DECISION` | (int64, float64) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `no` | `ML` | `STD` | (int8, int8) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `no` | `ML` | `STD` | (int16, int16) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `no` | `ML` | `STD` | (int32, float32) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `no` | `ML` | `STD` | (int64, float64) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `no` | `CHASE` | `STD` | (int8, int8) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `no` | `CHASE` | `STD` | (int16, int16) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `no` | `CHASE` | `STD` | (int32, float32) | 0, 1 | 0, 1 | 0, 1 | ✓ |
| `no` | `CHASE` | `STD` | (int64, float64) | 0, 1 | 0, 1 | 0, 1 | ✓ |
