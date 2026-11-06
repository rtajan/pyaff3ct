# Plan — pyaff3ct

Wrapper Python (pybind11) de la bibliothèque [AFF3CT](https://github.com/aff3ct/aff3ct), construit comme un
**extension de [pystreampu](https://github.com/aff3ct/pystreampu)** (paquet séparé qui dépend de `streampu`), reparti
de zéro : le prototype `_pyaff3ct` sert de retour d'expérience (guidelines, code, cf. §2).

Documents associés :

- [`docs/design/class_graph.md`](docs/design/class_graph.md) : graphe de toutes les classes à wrapper (Mermaid, généré).
- [`docs/design/inventory.md`](docs/design/inventory.md) : inventaire classe par classe (stratégie, priorité, nom Python, statut).
- [`docs/design/status.json`](docs/design/status.json) : statut de wrapping par classe (`Kind::Name` → `todo`/`wip`/`done`), seule source éditée à la main.
- [`docs/design/aff3ct_api.json`](docs/design/aff3ct_api.json) : empreinte de l'API AFF3CT de référence (cf. §7).
- [`docs/design/changes/`](docs/design/changes/) : rapports d'évolution d'AFF3CT.
- `scripts/` : `gen_class_graph.py` (graphe + inventaire), `aff3ct_api.py` (empreinte), `aff3ct_diff.py` (comparaison),
  `track_aff3ct.py` (suivi d'une révision à l'autre).

---

## 1. Objectifs

1. **Interaction Python fluide**, dans la philosophie pystreampu : un module AFF3CT *est* un `streampu.Module` ;
   ses tâches s'appellent comme des fonctions (`enc.encode(u)`), ses sockets se lisent en `numpy`, et les chaînes
   s'exécutent avec `streampu.Sequence` / `streampu.Pipeline`.
2. **Factory-first mais transparent** : la création passe par les factories AFF3CT dès qu'elles existent, pour garder
   le même comportement que la CLI `aff3ct` (validation, valeurs par défaut, choix des implémentations SIMD/template),
   **sans que l'utilisateur ait à manipuler la factory** : il appelle une fonction qui rend directement le module.
3. **Héritage fidèle** : chaque `py::class_` reproduit la chaîne d'héritage C++, interfaces StreamPU comprises.
4. **Séparation nette** : liaisons C++ dans `internal/`, API utilisateur dans `aff3ct/`.
5. **Couverture exhaustive mais pilotée** : l'inventaire généré sert de backlog, et chaque classe passe de `todo` à `done`.
6. **Suivi d'AFF3CT outillé** : chaque évolution amont produit un rapport d'impact sur les bindings (§7).

## 2. Ce qu'on garde et ce qu'on change par rapport à `_pyaff3ct`

| Guideline `_pyaff3ct` | Décision pour `pyaff3ct` |
|---|---|
| Arborescence `internal/include/internal/Wrapper/{Factory,Module,Tools}` + `internal/src/...` en miroir | **Conservée** (règle `.hpp`/`.hxx`/`.cpp` incluse) |
| Factory-first | **Conservé**, durci (classes à template de *politique* uniquement via factory) **et rendu transparent** (R5) |
| Héritage reproduit | **Conservé** ; les bases StreamPU sont **importées** de pystreampu, jamais re-wrappées |
| Constructeurs « avec des types classiques » | **Conservé** ; les types AFF3CT nécessaires aux constructeurs (tools) sont wrappés (cf. arêtes `uses` du graphe) |
| Une précision par build (implicite) | **Changé** : build `AFF3CT_MULTI_PREC`, choix du type au runtime via `dtype` (comme pystreampu) |
| Liste de classes à la main | **Changé** : inventaire généré depuis les en-têtes, donc reproductible et vérifiable |

État du prototype `_pyaff3ct` (consulté) : AFF3CT épinglé en **v4.1.2** (`60e113d`) ; wrappés : `CRC`,
`CRC_polynomial(_fast/_inter)`, `Decoder`/`_HIHO`/`_SIHO`/`_SISO`, `Encoder`, `Modem`, `Sparse_matrix`, `Galois`,
`RS_polynomial_generator`, constantes DVB-S2, et les factories Encoder/Decoder (LDPC, polar, RS, RSC, RSC_DB) + Modem ;
helpers `data_validator`, `str_operations`, `type_list`. Le rapport
`docs/design/changes/v4.1.2_60e113d4..v4.7.2_e1b52965.md` liste ce qui a bougé depuis : à reprendre en connaissance
de cause (helpers à relire en phase 1, rien à copier tel quel).

## 3. Architecture cible

### 3.1 Dépendances et édition de liens

```
aff3ct (Python)  ──import──▶  streampu (Python, pystreampu)
     │                              │
aff3ct._ext (pybind11)  ──py::module_::import("streampu")──▶  streampu._ext
     │                              │
libaff3ct (static, MULTI_PREC)      │
     └──────── link ──────▶  libstreampu statique (exportée par pystreampu, même commit)
```

Constats sur pystreampu (`develop` local, `c7318f4`) qui fixent le cadre :

- StreamPU **v1.10.0 `85ed022`**, exactement le commit épinglé par AFF3CT `develop` → l'ABI des `Task`/`Socket`/`Module`
  est commune ; `track_aff3ct.py` signale toute divergence future.
- pybind11 épinglé **3.0.4** (dépendance `pybind11>=3.0.4,<3.1`, *internals* v11) : pyaff3ct utilise la même contrainte.
- Python ≥ 3.10, y compris **3.14t sans GIL** : `PYBIND11_MODULE(_ext, m, py::mod_gil_not_used())` comme pystreampu,
  et aucune donnée globale mutable non protégée côté wrapper.
- Le modèle officiel d'extension (`examples/custom_cpp_module`) lie **sa propre copie statique** de StreamPU et refait
  `spu::tools::Buffer_allocator::set_task_autoalloc(true)` à l'import : pyaff3ct suit ce modèle (cf. risque 2).
- `streampu._ext.sfl` expose `Stateful` (C++ `spu::module::Stateful`) et `Stateful_core` (modules Python).

- Le module compilé `aff3ct._ext` fait `py::module_::import("streampu")` à l'initialisation. Les types
  `spu::module::Module`, `Stateful`, `Source`, `Sink`, `spu::runtime::Task`, `Socket`, les interfaces
  `spu::tools::Interface_*`, `Reporter`, `Terminal*` et `dtype` sont **ceux de pystreampu**.
- AFF3CT est compilé en **bibliothèque statique** (`AFF3CT_COMPILE_STATIC_LIB=ON`, `AFF3CT_COMPILE_EXE=OFF`,
  `-fPIC`, `AFF3CT_MULTI_PREC`), avec **`AFF3CT_INCLUDE_SPU_LIB=OFF`**, pour lier la StreamPU exportée par
  pystreampu (`streampu.get_cmake_dirs()`, comme dans `pystreampu/examples/custom_cpp_module`).
- Les helpers C++ de pystreampu (`wrapper/Common/Tools/type_list.hpp`, `type_functions.h`, `Type.hpp` : `dtype`,
  `ALL_DTYPES`, `str2typeid`…) sont réutilisés depuis les en-têtes installés par pystreampu.
- Aucun mécanisme d'enregistrement auprès de pystreampu (`streampu.plugins` n'existe plus) : `aff3ct` est un paquet
  autonome qui déclare `streampu` en dépendance et l'importe ; l'intégration repose uniquement sur le partage des
  types pybind11 (import de `streampu._ext` avant l'enregistrement des classes AFF3CT).

### 3.2 Build et packaging

- `scikit-build-core>=1.0` + `pybind11==3.0.4` (build) / `>=3.0.4,<3.1` (runtime) + `setuptools_scm`, C++17.
- `lib/aff3ct` en sous-module git, épinglé.
- Options CMake exposées via `-Ccmake.define.*` : précisions instanciées, `AFF3CT_LINK_GSL/MKL`, `-march`.
- Une unité de compilation par famille (`Encoder_polar.cpp`, `Decoder_LDPC.cpp`…) pour paralléliser et limiter la RAM.
  `ccache` et `CMAKE_UNITY_BUILD` sont activables en option.
- `cibuildwheel` (Linux x86_64/aarch64, macOS) en phase 5.

### 3.3 Arborescence

```
pyaff3ct/
├── CMakeLists.txt
├── pyproject.toml
├── lib/aff3ct/                       # sous-module AFF3CT (épinglé)
├── internal/
│   ├── include/internal/
│   │   ├── internal.hpp              # includes communs, py::module_::import("streampu")
│   │   ├── Common/Tools/             # dispatch dtype, casters (vector<bool>, Sparse_matrix, Noise), keep_alive helpers
│   │   └── Wrapper/
│   │       ├── Module/<Domaine>/<Classe>.hpp|.hxx
│   │       ├── Factory/<Domaine>/<Classe>.hpp|.hxx
│   │       └── Tools/<Domaine>/<Classe>.hpp|.hxx
│   └── src/
│       ├── ext.cpp                   # PYBIND11_MODULE(_ext, m)
│       └── Wrapper/...               # miroir exact de include/
├── aff3ct/                           # API Python
│   ├── __init__.py                   # sous-modules, version (aucun dtype défini ici)
│   ├── _dispatch.py                  # choix de l'instanciation C++ selon les dtypes
│   ├── crc.py chn.py dec.py enc.py ext.py itl.py mdm.py mnt.py pct.py qnt.py src.py cst.py
│   ├── factory/                      # factories (usage avancé : from_cli, params) ; cachées par défaut
│   ├── tools/                        # polar, ldpc, itl, cst, gen, turbo…
│   ├── codec.py reporter.py interfaces.py
│   └── py.typed + *.pyi              # stubs générés (pybind11-stubgen)
├── tests/
├── examples/
├── docs/                             # mkdocs (comme pystreampu) ; docs/design/* générés
└── scripts/                          # gen_class_graph, aff3ct_api, aff3ct_diff, track_aff3ct, gen_instantiations
```

Sous-modules Python = préfixes de factory AFF3CT (`crc`, `chn`, `cst`, `dec`, `enc`, `ext`, `itl`, `mdm`, `mnt`,
`pct`, `qnt`, `src`) : ce sont les mêmes que dans la CLI (`--enc-type`, `--dec-implem`…), donc rien de nouveau à apprendre.

## 4. Stratégie de wrapping (règles appliquées par l'inventaire)

Chiffres tirés de `docs/design/inventory.md` (AFF3CT `develop` @ `e1b5296`) :

| Espace | abstract | wrap | factory-only | fonctions | non exposé |
|---|---|---|---|---|---|
| `aff3ct::module` | 13 | 129 | 47 | – | – |
| `aff3ct::tools` | 23 | 66 | 16 (`Codec_*`) | 5 | 88 |
| `aff3ct::factory` | 1 | 83 | – | – | – |

**R1 — Héritage.** `py::class_<T, Base, Interfaces...>`, où les bases StreamPU proviennent du module importé. Exemple :
`Encoder_polar<B>` → `Encoder<B>` → (`spu::module::Stateful`, `spu::tools::Interface_set_seed`) +
`tools::Interface_get_set_frozen_bits`. Les interfaces AFF3CT (`Interface_get_set_frozen_bits`, `_noise`,
`_pretransform`, `_dynamic_frozen_bits`, `get_trellis`, `notify_noise_update`) sont liées une fois, sans constructeur.

**R2 — Bases abstraites (bleu).** `CRC`, `Channel`, `Coset`, `Decoder`/`_HIHO`/`_SIHO`/`_SISO`, `Encoder`,
`Extractor`, `Modem`, `Monitor`, `Puncturer`, `Quantizer` : aucun constructeur. On y lie les accesseurs communs
(`K`, `N`, `get_frozen_bits`, `is_sys`, `get_info_bits_pos`…) en `def_property`. Les tâches et sockets existent déjà
à l'exécution : l'accès `mod.encode`, `mod["encode::U_K"]` et l'appel `mod.encode(u)` viennent de la surcouche de
`streampu.Module`, sans code supplémentaire.

**R3 — Templates et dtypes.** pyaff3ct **ne définit aucun type de données** : les seuls dtypes sont ceux de
pystreampu (`streampu.dtype`, `spu.int8`, `spu.int16`, `spu.int32`, `spu.int64`, `spu.float32`, `spu.float64`),
côté Python comme côté C++ (`pyspu::dtype`, `pyspu::dtype::of<T>()`, `spu::runtime::type_to_string`,
`tl::type_list`). Il n'y a donc ni ré-export, ni alias, ni conversion : un socket produit par un module AFF3CT a le
même `dtype` qu'un socket pystreampu, et `spu.int32(x)` / `socket.astype(spu.float32)` s'appliquent directement.
Correspondance avec `Tools/types.h` : `B_8/Q_8 → spu.int8`, `B_16/Q_16 → spu.int16`, `B_32 → spu.int32`,
`B_64 → spu.int64`, `R_8/R_16/R_32/Q_32 → spu.float32`, `R_64/Q_64 → spu.float64`. Les dtypes non signés de
pystreampu (`uint*`) ne sont instanciés par aucun module AFF3CT : les passer lève une `TypeError` explicite.

Une classe template est instanciée **pour les seules combinaisons compilées par AFF3CT**
en `MULTI_PREC` (par exemple `Modem_BPSK<B,R,Q>` : `(i8,f32,f32)`, `(i8,f32,i8)`, `(i16,f32,f32)`, `(i16,f32,i16)`,
`(i32,f32,f32)`, `(i64,f64,f64)` ; `Decoder_*<B,Q>` : `(i8,i8)`, `(i16,i16)`, `(i32,f32)`, `(i64,f64)`).
`scripts/gen_instantiations.py` extrait ces listes des blocs `explicit template instantiation` des `.cpp`, ce qui
évite tout symbole manquant. Côté C++, les classes sont nommées `Encoder_polar_int32`, `Modem_BPSK_int32_float32_float32`
(convention pystreampu) ; côté Python, une fonction dispatch selon des `dtype` :

```python
import streampu as spu
enc = aff3ct.enc.polar(K, N, frozen_bits, dtype=spu.int32)         # -> _ext.enc.Encoder_polar_int32
mdm = aff3ct.mdm.bpsk(N, B=spu.int32, R=spu.float32)               # Q = R par défaut, comme en C++
```

Valeurs par défaut identiques aux défauts C++ (`B=spu.int32`, `R=Q=spu.float32`). Une combinaison absente lève une
`TypeError` qui liste les combinaisons disponibles.

**R4 — Factory-only (orange).** Les classes dont le template porte des paramètres de *politique* (`API_polar`,
`Update_rule`, `MAX`, pointeurs de fonctions `F/G/H`, `PSI`…) ne sont pas instanciées par le wrapper : la factory
choisit l'implémentation (`Decoder_polar` avec `implem="FAST"`, `Decoder_LDPC` avec `type="BP_HORIZONTAL_LAYERED"` et
`implem="NMS"`…). Le résultat est renvoyé sous le type enregistré le plus dérivé (polymorphisme pybind11) : par
exemple `Decoder_SIHO_int32_float32`, avec toutes ses tâches. Les familles intermédiaires sans politique
(`Decoder_LDPC_BP`, `Decoder_RSC_BCJR`, `Decoder_turbo`…) sont enregistrées pour exposer leurs accesseurs (`n_ite`…).

**R5 — Factories transparentes.** L'utilisateur ne crée pas de factory : il appelle la fonction de la famille, qui
rend le module prêt à l'emploi. En interne : instanciation de la factory, affectation des paramètres passés par
mots-clés, `build` avec les dtypes demandés.

```python
dec = af.dec.polar(K, N, frozen_bits, type="SCL", implem="FAST", L=8)    # Decoder_SIHO prêt à l'emploi
```

- Les mots-clés acceptés = paramètres publics de la factory (extraits dans `aff3ct_api.json` avec leurs défauts) +
  arguments de `build` (`frozen_bits`, `crc`, `encoder`…) + dtypes. Signatures, docstrings et stubs sont **générés**
  depuis l'empreinte : une évolution amont d'un paramètre de factory apparaît dans le rapport de suivi et se répercute
  par régénération.
- Un paramètre inconnu lève une `TypeError` qui liste les paramètres valides (pas d'affectation silencieuse).
- Sans factory (classe simple), la même fonction appelle directement le constructeur : l'utilisateur ne voit pas la
  différence.
- Usage avancé, explicitement opt-in dans `aff3ct.factory` : `from_cli("--dec-type SCL --dec-L 8")` (parité CLI via
  `cli::Argument_map_*`), `params`/`__repr__` (depuis `get_headers()`), `help()` (depuis `get_description()`), `clone()`.
  Une factory configurée s'utilise comme un « gabarit » : `fac(K=…)` rend un module.

**R6 — Ownership et durée de vie.**

- `build()` / constructeurs : `return_value_policy::take_ownership`.
- Objets gardés par référence dans un module : `py::keep_alive<1, n>()` sur le constructeur, et `<0, n>` sur `build()`.
  Cas recensés par les arêtes `uses` : `Interleaver(core)`, `Encoder_turbo(enc_n, enc_i, itl)`, `Decoder_turbo(siso_n, siso_i, itl)`,
  `Decoder_RA(itl)`, `Decoder_*_CA(crc)`, `Decoder_ML/chase(encoder)`, `Encoder_LDPC(G/H)`, `Decoder_LDPC_*(H)`,
  `Modem_generic(constellation)`, `Channel_*(generator)`, `Puncturer_polar(fb_generator)`. Pour chaque cas, on vérifie dans
  le source C++ s'il s'agit d'une copie ou d'une référence, et un test `gc.collect()` le couvre.
- `deep_copy` / `clone` des modules (utilisés par `Sequence` multi-thread) : on vérifie que les références internes
  sont re-câblées (comme le fait AFF3CT pour `Decoder_turbo`) avant d'exposer un module en multi-thread.

**R7 — Conversions de types (fluidité).**

| C++ | Python |
|---|---|
| `std::vector<bool>` (frozen bits) | `numpy.ndarray[bool]` (et liste acceptée) |
| `std::vector<T>` / `std::vector<std::vector<T>>` | `numpy.ndarray` / liste de listes |
| `tools::Sparse_matrix` | classe liée + `to_scipy()` / `from_scipy()` / `from_dense()` ; `aff3ct.tools.ldpc.read_alist(path)` |
| `tools::Noise<R>` (`Sigma`…) | classe liée + acceptation d'un `float` (`sigma=`) |
| enums `*_implem` (`STD`, `FAST`, `GSL`, `MKL`) | `py::enum_` + chaîne acceptée (`"FAST"`) |
| chemins de fichiers | `str` ou `os.PathLike` |
| fonctions `esn0_to_sigma`, `ebn0_to_esn0`, `sigma_to_esn0`, `esn0_to_ebn0` | `aff3ct.tools.*`, vectorisées numpy |

**R8 — Exceptions.** AFF3CT lève les exceptions `spu::tools::*` (`invalid_argument` ×313, `runtime_error` ×235…),
déjà traduites par pystreampu (`streampu.exceptions`). C'est valable seulement s'il n'y a qu'**une** copie de
StreamPU (cf. §3.1) ; sinon, on ré-enregistre les traducteurs dans `aff3ct._ext`.

**R9 — Non exposé.** 88 classes outils (API polaires SIMD, règles de mise à jour LDPC, réseaux de tri, PRNG, arbres,
`Reorderer`, constantes DVB-S2, `Contents_*`…) : ce sont des détails d'implémentation choisis par les factories.

**R10 — Documentation.** Docstrings `R"pbdoc(...)"` sur chaque classe, propriété et `build` (format Google, comme
pystreampu) ; stubs `.pyi` générés ; pages mkdocs générées depuis l'inventaire.

## 5. API Python visée (exemple de bout en bout)

```python
import numpy as np
import streampu as spu
import aff3ct as af

K, N, ebn0 = 512, 1024, 2.5
sigma = af.tools.esn0_to_sigma(af.tools.ebn0_to_esn0(ebn0, K / N))

fb  = af.tools.polar.frozen_bits(K, N, sigma, method="GA_Arikan")   # np.ndarray[bool]
src = af.src.random(K, dtype=spu.int32)                              # Source_random_fast<int32_t>
enc = af.enc.polar(K, N, fb)
mdm = af.mdm.bpsk(N)
chn = af.chn.awgn_llr(N, seed=42)
dec = af.dec.polar(K, N, fb, type="SC", implem="FAST")                 # factory Decoder_polar, cachée
mnt = af.mnt.bfer(K, max_fe=100)

cp  = spu.array([sigma], dtype=spu.float32)          # paramètre de canal (socket CP)
u   = src.generate()
y   = chn.add_noise(cp, mdm.modulate(enc.encode(u)))
v   = dec.decode_siho(mdm.demodulate(cp, y))
mnt.check_errors(u, v)

seq = spu.Sequence.from_socket(mnt["check_errors::status"], n_threads=8)
seq.exec()                                              # arrêt : Monitor_BFER implémente Interface_is_done
print(af.reporter.Reporter_BFER(mnt))
```

Les noms des tâches et sockets sont ceux d'AFF3CT (`generate`, `encode`, `modulate`, `add_noise`,
`demodulate(CP, Y_N1)`, `decode_siho`, `check_errors`). L'appel et le binding par position ou par nom suivent les
règles de pystreampu. Deux helpers restent à créer : `af.tools.polar.frozen_bits` (sucre au-dessus de
`Frozenbits_generator_*`) et l'arrêt de `Sequence.exec()` via le moniteur (à valider dès la phase 2 ; sinon,
`exec_n_times` ou un `stop_condition` à exposer dans pystreampu).

## 6. Feuille de route

Chaque phase se termine par une MR, et sa **Definition of Done** inclut : compilation OK, `pytest` vert,
inventaire mis à jour (`done`), docstrings présentes.

### Phase 0 — Amorçage du dépôt
- `pyproject.toml`, `CMakeLists.txt`, sous-module `lib/aff3ct` épinglé, CI (build + tests sur Linux/macOS).
- `aff3ct._ext` vide qui importe `streampu` ; `aff3ct.__version__`.
- **Vérification bloquante** : un objet AFF3CT créé côté `aff3ct._ext` est manipulable par `streampu` (Task, Socket,
  Sequence, exception traduite) avec une seule StreamPU liée.
- DoD : `pip install .` puis `python -c "import aff3ct"` (qui importe `streampu` en interne) ; un module AFF3CT est
  reconnu comme `streampu.Stateful` (`isinstance`).

### Phase 1 — Socle (infrastructure générique)
- `internal/include/internal/Common/Tools` : dispatch des instanciations (listes générées par `gen_instantiations.py`),
  casters (`vector<bool>`, numpy), helpers `keep_alive`, macros de docstring.
- Interfaces AFF3CT (6) + 13 bases abstraites de modules + `factory::Factory` (params/headers/CLI).
- Mécanique des factories transparentes (R5) : générateur des fonctions de famille depuis `aff3ct_api.json`.
- `aff3ct/_dispatch.py` : résolution des `streampu.dtype` → classe C++ (nom construit avec `dtype.name`, comme
  `streampu._incrementer`), avec un message d'erreur listant les combinaisons disponibles.
- DoD : tests de dispatch et d'héritage (`isinstance(enc, streampu.Stateful)`, `Interface_set_seed`…).

### Phase 2 — MVP : chaîne BFER complète (priorité **P0**, 93 entrées)
- Modules : `Source_random_fast`, `CRC_polynomial/NO`, `Encoder_{NO,polar,polar_sys,LDPC,LDPC_from_H,BCH,RS,repetition_sys}`,
  `Modem_BPSK(_fast)`, `Channel_{AWGN_LLR,NO}`, `Quantizer_{NO,pow2}`, `Decoder_{NO,repetition,BCH_std,RS_std}` +
  polaire SC et LDPC BP via factory, `Interleaver`, `Puncturer_NO`, `Monitor_BFER`.
- Tools : `Sparse_matrix` + lecture AList, `BCH/RS_polynomial_generator` (+ `Galois`), `Frozenbits_generator_{GA_Arikan,BEC,file}`,
  `Interleaver_core_{NO,random,LTE,user}`, `Sigma`, `Reporter_{BFER,noise,throughput}` (avec `spu.Terminal_std`).
- Factories P0 correspondantes.
- **Validation numérique** : courbes BER/FER comparées aux références `lib/aff3ct/refs` (polaire SC, LDPC BP, BCH)
  à tolérance statistique près.
- Exemples `examples/polar_bfer.py`, `examples/ldpc_bfer.py`, et notebook.

### Phase 3 — Couverture cœur (priorité **P1**, 229 entrées)
- Toutes les familles restantes « mainstream » : Turbo/RSC (+ `Post_processing_SISO`, `Flip_and_check`, `Scaling_factor`),
  RA, Repetition, Conv/Viterbi, Polar SCL/ASCL/SCF/SCAN, LDPC (toutes les règles via factory), Modem générique
  (`Constellation_*`), OOK, Rayleigh, BEC/BSC, `Extractor_*`, `Puncturer_*`, `Quantizer_custom`, générateurs de bruit.
- `Codec_*` (via factories) : propriétés `encoder`, `decoder_siso`, `decoder_siho`, `extractor`, `puncturer`.
- DoD : un test de construction et d'exécution par classe, et un test de parité CLI par factory.

### Phase 4 — Avancé (priorité **P2**, 51 entrées)
- Polar MK / PAC / PT (`Polar_code`, `Pretransform_generator`), SCMA, CPM, optique (`Distributions`), `Channel_user*`,
  Monitors EXIT/MI et leurs reporters, Turbo product, variantes AVX/SSE, `Monitor_reduction` (multi-thread).

### Phase 5 — Industrialisation (priorité **P3** inclus)
- Docs mkdocs (API générée, guides, galerie d'exemples), stubs `.pyi`, wheels `cibuildwheel`, publication.
- Outils de debug optionnels : `Dumper`, `Frame_trace`, `Histogram`, générateurs GSL/MKL.

## 7. Suivi des évolutions d'AFF3CT

Principe : l'API d'AFF3CT dont dépendent les bindings est réduite à une **empreinte** versionnée
(`docs/design/aff3ct_api.json`, produite par `scripts/aff3ct_api.py`). Pour chaque classe : en-tête, paramètres
template, bases, constructeurs (types **et** valeurs par défaut), méthodes publiques, paramètres publics des factories
(avec défauts), tâches et sockets (direction, type, ordre — l'ordre conditionne l'appel positionnel Python),
instanciations `MULTI_PREC` (classes et `build<…>`, donc les combinaisons de dtypes disponibles) ; plus les commits des
sous-modules StreamPU et cli.

Comparer deux empreintes (`aff3ct_diff.py`) classe chaque changement :

| Niveau | Exemples | Conséquence |
|---|---|---|
| Cassant | classe/constructeur/méthode/tâche/socket/paramètre/instanciation supprimé ou modifié, base changée, en-tête déplacé | binding ou API Python à modifier |
| Défauts | valeur par défaut modifiée (constructeur, paramètre de factory, `build`) | défauts Python à aligner |
| Ajout | nouvelle classe (avec sa stratégie et priorité calculées), constructeur, paramètre, tâche, instanciation | backlog |
| Réorganisation | méthode désormais héritée d'une base | vérification rapide |

Chaque changement est croisé avec `status.json` : un changement cassant ou de défaut sur une classe `done`/`wip` est
une **action requise**, mise en tête du rapport ; `--fail-on-impact` rend alors le code de sortie 1 (CI).

Utilisation :

```bash
# Quoi de neuf en amont depuis la référence de pyaff3ct ?
python3 scripts/track_aff3ct.py --repo lib/aff3ct --fetch --to origin/develop
# Montée de version acceptée : nouvelle référence + graphe + inventaire régénérés
python3 scripts/track_aff3ct.py --repo lib/aff3ct --to <ref> --update
```

Les révisions sont extraites dans des `git worktree` temporaires : le sous-module de travail n'est jamais touché.

Validé sur deux cas réels :
- `v4.1.2 → v4.7.2` (écart `_pyaff3ct` → aujourd'hui) : 13 cassants (ajout de `Syndrome_checker` aux décodeurs LDPC BP,
  Viterbi déplacé de `RSC/` vers `Conv/`, `Encoder_polar_PAC` qui hérite d'`Encoder_polar`…), 1 défaut, 42 ajouts ;
- `ec05893^ → v4.7.2` (Polar PT + encodeur bitpacked) : 1 cassant, 24 ajouts, 3 réorganisations, changement de
  StreamPU signalé.

Organisation proposée :
1. **CI planifiée (hebdomadaire)** : `track_aff3ct.py --fetch --to origin/develop --fail-on-impact` ; le rapport est
   publié comme artefact, et une issue est ouverte (ou mise à jour) s'il y a des changements.
2. **Montée du sous-module** = une MR dédiée qui contient : bump de `lib/aff3ct`, `--update` (empreinte, graphe,
   inventaire), le rapport dans `docs/design/changes/`, et les corrections de bindings pour chaque action requise.
3. **Test de cohérence** (dès la phase 1) : chaque classe `done` de `status.json` doit exister dans `aff3ct._ext` avec
   ses tâches/sockets conformes à l'empreinte ; une classe wrappée absente de `status.json` fait aussi échouer le test.
4. Alignement StreamPU : le rapport signale tout changement du sous-module StreamPU d'AFF3CT, à confronter au commit
   épinglé par pystreampu avant d'accepter la montée.

## 8. Stratégie de tests

| Niveau | Contenu |
|---|---|
| Unitaire | construction pour chaque combinaison de dtypes pystreampu ; `uint*` refusés ; propriétés ; erreurs (`TypeError` dtype, `ValueError` paramètres) |
| Tâches | exécution d'une tâche sur des entrées `numpy` connues (ex. encodeur systématique : `U == X[sys]`) |
| Factory | `build()` vs construction directe ; `from_cli()` vs paramètres Python ; `params` vs `get_headers` |
| Durée de vie | création d'objets dépendants, suppression des références Python, `gc.collect()`, exécution |
| Multi-thread | `Sequence(n_threads>1)` sur une chaîne complète (vérifie clone/deep_copy) |
| Numérique | BER/FER vs `refs/` AFF3CT sur quelques points d'Eb/N0 (marquage `@pytest.mark.slow`) |

## 9. Risques et points ouverts

1. **Version de StreamPU** : *résolu à date* (pystreampu et AFF3CT sur `85ed022`, v1.10.0) ; surveillé par le suivi (§7).
2. **Deux copies statiques de StreamPU** (modèle officiel des extensions) : états globaux dupliqués
   (`set_task_autoalloc` refait à l'import ; `Signal_handler`, `type_to_string`) et `typeid` potentiellement distincts
   avec `-fvisibility=hidden` (traduction des exceptions `spu::tools::*`, downcast polymorphe). À vérifier en phase 1
   par des tests dédiés ; repli : ré-enregistrer les traducteurs d'exceptions dans `aff3ct._ext`.
3. **ABI pybind11** : même contrainte que pystreampu (`>=3.0.4,<3.1`, même compilateur et stdlib), contrôlée en CI.
4. **Temps de compilation et taille binaire** : environ 190 classes × 4 à 6 instanciations. Leviers : une TU par famille,
   option CMake pour restreindre les précisions (`PYAFF3CT_PRECISIONS=32` en dev), ccache, LTO uniquement en release.
5. **Références internes et `clone()`** : certains modules (turbo, CA) gardent des références vers d'autres objets ;
   à auditer famille par famille (R6).
6. **Dépendances optionnelles** (GSL, MKL, MPI) : désactivées par défaut, exposées seulement si compilées.
7. **Évolution AFF3CT** : couverte par §7 ; limite connue : l'empreinte est extraite par analyse textuelle des
   en-têtes (pas de compilateur), donc une construction C++ inhabituelle peut échapper au diff — les tests de
   cohérence (§7, point 3) servent de filet.
8. **Sans GIL (3.14t)** : les modules AFF3CT exécutés par `Sequence` multi-thread n'appellent pas Python ; les seuls
   callbacks Python (reporters, conditions d'arrêt) reprennent le GIL comme dans pystreampu.

## 10. Conventions de contribution

- Branches `feat/<domaine>-<famille>`, `fix/...` ; une MR par famille ou phase.
- Messages de commit à l'impératif, préfixés par le domaine (`enc: wrap Encoder_polar`, `factory: add Decoder_LDPC build`).
- Toute MR met à jour `docs/design/status.json` (puis régénère `inventory.md`) et ajoute ses tests.
- Checklist MR (reprise des guidelines) : miroir include/src respecté, compilation et import OK, API Python documentée,
  tests ajoutés, chemins et noms de classes corrects dans la doc.
