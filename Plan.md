# Plan — pyaff3ct

Wrapper Python (pybind11) de la bibliothèque [AFF3CT](https://github.com/aff3ct/aff3ct), construit comme un
**plugin de [pystreampu](https://github.com/aff3ct/pystreampu)** et reparti de zéro (le prototype `_pyaff3ct` sert
uniquement de retour d'expérience, via ses *Development Guidelines*).

Documents associés :

- [`docs/design/class_graph.md`](docs/design/class_graph.md) : graphe de toutes les classes à wrapper (Mermaid, généré).
- [`docs/design/inventory.md`](docs/design/inventory.md) : inventaire classe par classe (stratégie, priorité, nom Python, statut).
- [`scripts/gen_class_graph.py`](scripts/gen_class_graph.py) : générateur des deux documents ci-dessus à partir des en-têtes AFF3CT.

---

## 1. Objectifs

1. **Interaction Python fluide**, dans la philosophie pystreampu : un module AFF3CT *est* un `streampu.Module` ;
   ses tâches s'appellent comme des fonctions (`enc.encode(u)`), ses sockets se lisent en `numpy`, et les chaînes
   s'exécutent avec `streampu.Sequence` / `streampu.Pipeline`.
2. **Factory-first** : la création passe par les factories AFF3CT dès qu'elles existent, pour garder le même
   comportement que la CLI `aff3ct` (validation, valeurs par défaut, choix des implémentations SIMD/template).
3. **Héritage fidèle** : chaque `py::class_` reproduit la chaîne d'héritage C++, interfaces StreamPU comprises.
4. **Séparation nette** : liaisons C++ dans `internal/`, API utilisateur dans `aff3ct/`.
5. **Couverture exhaustive mais pilotée** : l'inventaire généré sert de backlog, et chaque classe passe de `todo` à `done`.

## 2. Ce qu'on garde et ce qu'on change par rapport à `_pyaff3ct`

| Guideline `_pyaff3ct` | Décision pour `pyaff3ct` |
|---|---|
| Arborescence `internal/include/internal/Wrapper/{Factory,Module,Tools}` + `internal/src/...` en miroir | **Conservée** (règle `.hpp`/`.hxx`/`.cpp` incluse) |
| Factory-first | **Conservé**, et durci : les classes à paramètres template de *politique* ne sont **que** via factory |
| Héritage reproduit | **Conservé** ; les bases StreamPU sont **importées** de pystreampu, jamais re-wrappées |
| Constructeurs « avec des types classiques » | **Conservé** ; les types AFF3CT nécessaires aux constructeurs (tools) sont wrappés (cf. arêtes `uses` du graphe) |
| Une précision par build (implicite) | **Changé** : build `AFF3CT_MULTI_PREC`, choix du type au runtime via `dtype` (comme pystreampu) |
| Liste de classes à la main | **Changé** : inventaire généré depuis les en-têtes, donc reproductible et vérifiable |

Le dépôt `_pyaff3ct` n'a pas été consulté directement (inaccessible depuis l'environnement de travail). Si des
choix d'implémentation y méritent d'être repris (helpers, caster numpy, tests), il faudra les intégrer en phase 1.

## 3. Architecture cible

### 3.1 Dépendances et édition de liens

```
aff3ct (Python)  ──import──▶  streampu (Python, pystreampu)
     │                              │
aff3ct._ext (pybind11)  ──py::module_::import("streampu")──▶  streampu._ext
     │                              │
libaff3ct (static, MULTI_PREC)      │
     └──────── link ──────▶  libstreampu  (UNE seule copie, celle livrée par pystreampu)
```

- Le module compilé `aff3ct._ext` fait `py::module_::import("streampu")` à l'initialisation. Les types
  `spu::module::Module`, `Stateful`, `Source`, `Sink`, `spu::runtime::Task`, `Socket`, les interfaces
  `spu::tools::Interface_*`, `Reporter`, `Terminal*` et `dtype` sont **ceux de pystreampu**.
- AFF3CT est compilé en **bibliothèque statique** (`AFF3CT_COMPILE_STATIC_LIB=ON`, `AFF3CT_COMPILE_EXE=OFF`,
  `-fPIC`, `AFF3CT_MULTI_PREC`), avec **`AFF3CT_INCLUDE_SPU_LIB=OFF`**, pour lier la StreamPU exportée par
  pystreampu (`streampu.utils.get_cmake_dirs()`, comme dans `pystreampu/examples/custom_cpp_module`).
- Les helpers C++ de pystreampu (`wrapper/Common/Tools/type_list.hpp`, `type_functions.h`, `Type.hpp` : `dtype`,
  `ALL_DTYPES`, `str2typeid`…) sont réutilisés depuis les en-têtes installés par pystreampu.
- Le paquet s'enregistre comme plugin : `entry_points` du groupe `streampu.plugins` (`aff3ct = "aff3ct"`), donc
  `streampu.plugins["aff3ct"]` fonctionne.

### 3.2 Build et packaging

- `scikit-build-core` + `pybind11>=3` + `setuptools_scm` (même chaîne que pystreampu), C++17.
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
│   ├── factory/                      # surcouche Pythonique des factories
│   ├── tools/                        # polar, ldpc, itl, cst, gen, turbo…
│   ├── codec.py reporter.py interfaces.py
│   └── py.typed + *.pyi              # stubs générés (pybind11-stubgen)
├── tests/
├── examples/
├── docs/                             # mkdocs (comme pystreampu) ; docs/design/* générés
└── scripts/gen_class_graph.py, scripts/gen_instantiations.py
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

**R5 — Factories (API Pythonique).**

- Chaque paramètre public (`K`, `N_cw`, `type`, `implem`, `n_ite`…) devient un `def_readwrite`.
- Constructeur à mots-clés et chaînage : `aff3ct.factory.Decoder_polar(K=K, N_cw=N, type="SCL", implem="FAST", L=8)`.
- `build(..., B=..., Q=...)` dispatche vers les `build<B,Q>` instanciés ; `build_siso`, `build_gen`… suivent le même modèle.
- `store(argv)` / `from_cli("--dec-type SCL --dec-L 8")` réutilisent `cli::Argument_map_*`, d'où une parité exacte avec la CLI.
- `params` (dict) et `__repr__` sont construits depuis `get_headers()` ; `help()` provient de `get_description()`.
- `clone()` est lié via `spu::tools::Interface_clone`.

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
dec = af.factory.Decoder_polar(K=K, N_cw=N, type="SC", implem="FAST").build(fb)
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
- `aff3ct._ext` vide qui importe `streampu` ; entry point `streampu.plugins` ; `aff3ct.__version__`.
- **Vérification bloquante** : un objet AFF3CT créé côté `aff3ct._ext` est manipulable par `streampu` (Task, Socket,
  Sequence, exception traduite) avec une seule StreamPU liée.
- DoD : `pip install .` puis `python -c "import streampu, aff3ct"` ; `streampu.plugins["aff3ct"]` est présent.

### Phase 1 — Socle (infrastructure générique)
- `internal/include/internal/Common/Tools` : dispatch des instanciations (listes générées par `gen_instantiations.py`),
  casters (`vector<bool>`, numpy), helpers `keep_alive`, macros de docstring.
- Interfaces AFF3CT (6) + 13 bases abstraites de modules + `factory::Factory` (params/headers/CLI).
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

## 7. Stratégie de tests

| Niveau | Contenu |
|---|---|
| Unitaire | construction pour chaque combinaison de dtypes pystreampu ; `uint*` refusés ; propriétés ; erreurs (`TypeError` dtype, `ValueError` paramètres) |
| Tâches | exécution d'une tâche sur des entrées `numpy` connues (ex. encodeur systématique : `U == X[sys]`) |
| Factory | `build()` vs construction directe ; `from_cli()` vs paramètres Python ; `params` vs `get_headers` |
| Durée de vie | création d'objets dépendants, suppression des références Python, `gc.collect()`, exécution |
| Multi-thread | `Sequence(n_threads>1)` sur une chaîne complète (vérifie clone/deep_copy) |
| Numérique | BER/FER vs `refs/` AFF3CT sur quelques points d'Eb/N0 (marquage `@pytest.mark.slow`) |

## 8. Risques et points ouverts

1. **Version de StreamPU divergente** : AFF3CT `develop` épingle `lib/streampu@85ed022`, pystreampu `develop`
   épingle `lib/streampu@cf60c36`. Il faut aligner (même commit, ou API compatible) **avant** la phase 0, sinon l'ABI
   des objets partagés (`Task`, `Socket`, `Module`) n'est pas garantie.
2. **Copie unique de StreamPU** : deux copies statiques dupliqueraient les états globaux
   (`Buffer_allocator::set_task_autoalloc`, `Signal_handler`, tables `type_to_string`) et casseraient la
   comparaison de `typeid` (traduction d'exceptions, downcast) avec `-fvisibility=hidden`. Cible : lier la StreamPU de
   pystreampu, ou idéalement une `libstreampu` partagée exportée par pystreampu (à proposer en amont).
3. **ABI pybind11** : `streampu._ext` et `aff3ct._ext` doivent partager les *internals* pybind11 (même version majeure,
   même compilateur et même stdlib). À contrôler dans la CI, et à documenter pour les builds depuis les sources.
4. **Temps de compilation et taille binaire** : environ 190 classes × 4 à 6 instanciations. Leviers : une TU par famille,
   option CMake pour restreindre les précisions (`PYAFF3CT_PRECISIONS=32` en dev), ccache, LTO uniquement en release.
5. **Références internes et `clone()`** : certains modules (turbo, CA) gardent des références vers d'autres objets ;
   à auditer famille par famille (R6).
6. **Dépendances optionnelles** (GSL, MKL, MPI) : désactivées par défaut, exposées seulement si compilées.
7. **Évolution AFF3CT** : relancer `scripts/gen_class_graph.py` à chaque montée du sous-module, puis comparer
   l'inventaire (`inventory.json`) pour détecter classes ajoutées ou supprimées.

## 9. Conventions de contribution

- Branches `feat/<domaine>-<famille>`, `fix/...` ; une MR par famille ou phase.
- Messages de commit à l'impératif, préfixés par le domaine (`enc: wrap Encoder_polar`, `factory: add Decoder_LDPC build`).
- Toute MR met à jour `docs/design/inventory.md` (statut) et ajoute ses tests.
- Checklist MR (reprise des guidelines) : miroir include/src respecté, compilation et import OK, API Python documentée,
  tests ajoutés, chemins et noms de classes corrects dans la doc.
