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
`Extractor`, `Modem`, `Monitor`, `Puncturer`, `Quantizer` : aucun constructeur. On y lie les accesseurs communs.
Les tâches et sockets existent déjà à l'exécution : l'accès `mod.encode`, `mod["encode::U_K"]` et l'appel
`mod.encode(u)` viennent de la surcouche de `streampu.Module`, sans code supplémentaire.

*Convention des accesseurs (comme pystreampu)* : `get_X()` → propriété en lecture seule `X` (`enc.K`, `enc.N`,
`enc.info_bits_pos`) ; `is_X()` et `set_X()` restent des méthodes (`enc.is_sys()`, `dec.set_auto_reset(False)`,
`mdm.is_filter()`). Aucune propriété en écriture sur les modules. pystreampu atteint les tâches par
`Module.__getattr__` (repli) : un attribut portant le nom d'une tâche la masquerait (`Modem.filter`) ; un test
(`test_no_attribute_hides_a_task`) le vérifie pour toutes les classes wrappées, à partir des tâches de l'empreinte.

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
(convention pystreampu) ; côté Python, les dtypes se donnent sous les noms des paramètres template AFF3CT (`B=`,
`R=`, `Q=`…), ou `dtype=` quand il n'y en a qu'un :

```python
import streampu as spu
enc = aff3ct.enc.polar(K, N, frozen_bits, B=spu.int64)              # -> _ext.enc.Encoder_polar_int64
mdm = aff3ct.mdm.bpsk(N, B=spu.int16, R=spu.float32, Q=spu.int16)
dec = aff3ct.dec.polar(K, N, frozen_bits, B=spu.int8)               # Q = int8 : seule valeur compilée avec B=int8
```

Résolution (`aff3ct/_dispatch.py`) : les dtypes donnés sont gardés ; un paramètre absent prend la **seule valeur
compatible** avec les autres quand elle est unique (`B=int8` ⇒ `Q=int8`), sinon son **défaut**. Les défauts de `B`,
`R` et `Q` sont ceux de la précision 32 bits de la CLI AFF3CT (`B=int32`, `R=Q=float32`) et non les défauts C++
littéraux, qui peuvent désigner une combinaison non compilée (`Quantizer<R = float, Q = int>`) ; `Q = R` est respecté.
Une combinaison absente ou ambiguë lève une `TypeError` qui liste les combinaisons disponibles.

*Templates indexables* : chaque sous-module Python regroupe les instances d'une classe template
(`_ext.enc.Encoder_int8` … `Encoder_int64`) en un objet `Template` : `isinstance(enc, af.enc.Encoder)` quel que soit
`B`, `af.enc.Encoder[spu.int16]` pour une instance, `af.dec.Decoder_SIHO[spu.int32, spu.float32]`. Les noms suffixés
restent dans `aff3ct._ext` ; le regroupement est automatique (`aff3ct._dispatch.export`), les classes ajoutées
apparaissent donc sans code Python.

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
dec = af.dec.polar(K, N_cw=N, frozen_bits=fb, type="SCL", implem="FAST", L=8)    # Decoder_SIHO prêt à l'emploi
```

Les paramètres gardent **les noms des attributs des factories AFF3CT** (`N_cw`, `type`, `implem`, `n_ite`, `L`…),
sans table de traduction à maintenir.

- Les mots-clés acceptés = paramètres publics de la factory (extraits dans `aff3ct_api.json` avec leurs défauts) +
  arguments de `build` (`frozen_bits`, `crc`, `encoder`…) + dtypes. Signatures, docstrings et stubs sont **générés**
  depuis l'empreinte : une évolution amont d'un paramètre de factory apparaît dans le rapport de suivi et se répercute
  par régénération.
- Un paramètre inconnu lève une `TypeError` qui liste les paramètres valides (pas d'affectation silencieuse).
- Sans factory (classe simple), la même fonction appelle directement le constructeur : l'utilisateur ne voit pas la
  différence.
- Usage avancé, explicitement opt-in dans `aff3ct.factory` (les fonctions suffisent au quotidien) :

  ```python
  f = af.factory.Decoder_polar.from_cli("--dec-type SCL --dec-L 8")   # sur la classe : crée la factory
  f.K, f.N_cw = K, N                                                  # paramètres = attributs
  f.from_cli("--dec-implem NAIVE")                                    # sur une instance : la met à jour
  dec = f.build(fb, B=spu.int16)                                      # builder choisi selon les dtypes
  f.parameters, f.headers(), f.print_help(), f.clone()
  ```

  `from_cli` passe par le parseur `cli::Argument_handler` d'AFF3CT (parité exacte avec la CLI) ; un argument inconnu
  ou d'une autre factory lève une `ValueError`.

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
traduites par pystreampu (`streampu.exceptions`). *Vérifié en phase 1* malgré la copie statique de StreamPU propre à
`aff3ct._ext` : une erreur levée dans libaff3ct arrive en `streampu.exceptions.InvalidArgument` avec le message
AFF3CT complet (`test_aff3ct_exceptions_are_the_streampu_ones`). Les erreurs propres au wrapper sont des exceptions
Python standards (`TypeError` pour les dtypes et paramètres inconnus, `ValueError` pour la CLI).

**R8 bis — Type des modules renvoyés par pystreampu.** pybind11 type un `Module*` renvoyé (modules d'une `Sequence`,
`task.module`…) d'après son type dynamique exact ; si cette classe concrète n'est pas enregistrée
(`CRC_polynomial_fast<int>`, et surtout les 47 classes « factory-only »), il retombe sur `Module` : les tâches restent
utilisables mais les accesseurs AFF3CT sont perdus. *Constaté en phase 1*. **Décision et réalisation** : registre de
« downcasters » dans pystreampu (mergé sur `develop`, en-tête
`wrapper/Common/Tools/Module_downcast.hpp`) — spécialisation de `pybind11::polymorphic_type_hook<spu::module::Module>`
qui, pour un type dynamique non enregistré, interroge les downcasters inscrits par les extensions (stockés dans les
*shared data* des internals pybind11, donc partagés malgré les copies de StreamPU ; mutex pour le mode sans GIL).
Côté pyaff3ct, chaque `py::class_` de module appelle `add_module_class<T>()` (bases d'abord) et un seul downcaster
renvoie la classe enregistrée la plus dérivée (`internal/Common/Tools/downcast.hpp`). Détection à la compilation
(`__has_include`, `aff3ct._ext.HAS_STREAMPU_DOWNCAST_REGISTRY`) : avec un pystreampu sans registre, tout fonctionne
sauf ce typage (test en `xfail`). Tests : clones d'une `Sequence` à 2 threads typés `CRC_int16` avec leurs
accesseurs ; toute classe de module enregistrée est inscrite (`_N_MODULE_CLASSES`). La CI construit pystreampu
depuis `develop` ; à faire à sa prochaine publication : exiger cette version de streampu dans `pyproject.toml`.

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
src = af.src.random(K, B=spu.int32)                                  # Source_random_fast<int32_t>
enc = af.enc.polar(K, N_cw=N, frozen_bits=fb)
mdm = af.mdm.bpsk(N)
chn = af.chn.awgn_llr(N, seed=42)
dec = af.dec.polar(K, N_cw=N, frozen_bits=fb, type="SC", implem="FAST")   # factory Decoder_polar, cachée
mnt = af.mnt.bfer(K, max_fe=100)

cp  = spu.array([sigma], dtype=spu.float32)          # paramètre de canal (socket CP)
u   = src.generate()[0]                               # generate -> (out_data, out_count), comme pystreampu
y   = chn.add_noise(cp, mdm.modulate(enc.encode(u)))
v   = dec.decode_siho(mdm.demodulate(cp, y))
mnt.check_errors(u, v)

seq = spu.Sequence(mnt["check_errors::status"], n_threads=8)   # API de pystreampu
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

### Phase 0 — Amorçage du dépôt ✅ (livrée avec la phase 1)
- `pyproject.toml` (scikit-build-core, `pybind11==3.0.4`, `streampu` requis au build), `CMakeLists.txt`, sous-module
  `lib/aff3ct` épinglé sur `e1b5296` (v4.7.2) avec ses sous-modules `cli` (+ `rang`), `MIPP`, `date`.
- AFF3CT compilé en statique `MULTI_PREC`, `AFF3CT_INCLUDE_SPU_LIB=OFF`, lié à la StreamPU installée par pystreampu
  (`find_package(cpptrace)` puis `find_package(StreamPU)`, comme `examples/custom_cpp_module`).
- Base SIMD commune `PYAFF3CT_ARCH_FLAGS` (défaut `-msse4.2` sur x86-64 : MIPP s'arrête à l'exécution avec la base
  SSE2, cf. AFF3CT `420db34` ; `-march=native` pour un build local).
- `scripts/dev_build.sh` : build de développement (`build/dev`) et lien de `_ext` dans `aff3ct/` pour `pytest`.
- Reste à faire : CI (build + tests Linux/macOS) et vérification du `pip install .` complet.

### Phase 1 — Socle (infrastructure générique) ✅
- `internal/include/internal/Common/Tools` : `combos.hpp` / `dtypes.hpp` (enregistrement d'une classe par
  combinaison de dtypes, noms suffixés pystreampu), `casters.hpp` (`std::vector<bool>` ↔ `numpy.ndarray[bool]`).
- `scripts/gen_instantiations.py` → `internal/include/internal/Generated/instantiations.hpp` et
  `aff3ct/_generated/instantiations.py` : combinaisons compilées (201 templates, 81 builders de factory), défauts
  précision 32 bits.
- Interfaces AFF3CT (6), 13 bases abstraites de modules (convention d'accesseurs R2), `Noise` / `Sigma` /
  `Event_probability` / `Received_optical_power`.
- `factory::Factory` : `from_cli` (classe ou instance), `parameters`, `headers`, `print_help`, `clone`, paramètres par
  mots-clés, builders choisis selon les dtypes ; moteur des factories transparentes `_factory.build`.
  Factory jouet : `CRC` (construit de vrais modules dont les tâches s'exécutent via pystreampu).
- `aff3ct/_dispatch.py` : résolution des dtypes et `Template` indexables, export automatique par sous-module.
- Tests : import, dispatch (dont `uint*` refusés), héritage pystreampu, convention d'accesseurs, absence de conflit
  attribut/tâche, casters, bruit, factory (mots-clés ≡ `from_cli`, erreurs, `headers`, `clone`, build par dtype,
  exécution des tâches `build`/`extract` d'un CRC).

### Phase 2 — MVP : chaîne BFER complète (priorité **P0**, 93 entrées)
- **D'abord** ✅ : générateur `scripts/gen_factories.py` (depuis `aff3ct_api.json`, `instantiations.py` et
  `status.json`) → une unité C++ par factory (79 factories, 88 builders : paramètres `def_param`, sous-factories en
  références, builders par dtype, builders non templates en `_<builder>_raw`) et `aff3ct/_generated/functions.py`
  (55 fonctions de famille, exportées par chaque sous-module). Règles appliquées :
  - **Positionnels** : les tailles (`K`, `N_cw`, `N`) de la factory la plus haute de la famille qui en déclare
    (`Decoder` → `K, N_cw` ; `Monitor_BFER` → `K` ; le `N` de `Decoder_LDPC` reste un mot-clé), puis les arguments du
    builder ; **mots-clés seuls** : tous les autres paramètres (`None` = défaut AFF3CT) et les dtypes (`B=`, `Q=`…).
  - **Un builder = une fonction** : `polar` (`build`), `polar_siso`, `polar_gen` ; les surcharges d'un builder
    (`Channel.build()` / `build(dist)`) sont fusionnées, pybind11 choisit d'après les arguments donnés.
  - Arguments optionnels : liés aussi en surcharges tronquées (pybind11 ne charge pas `None` vers un pointeur de type
    non wrappé) ; un défaut non littéral (`std::ostream& stream = std::cout`) n'est pas exposé.
  - Une fonction n'est générée que si la classe renvoyée est wrappée (module : une base wrappée suffit, grâce au
    registre de downcasters ; outil : le type exact) ; les autres sont listées dans `SKIPPED` (28 : `Codec_*`,
    `Frozenbits_generator`, `Interleaver_core`, `Constellation`…) et apparaîtront en wrappant ces outils.
  - `Codec` et `Decoder` (bases de famille) sont liées sans constructeur ; `Terminal.build` est écarté
    (`vector<unique_ptr<Reporter>>`, utiliser `streampu.Terminal_std`).
  - Convention AFF3CT à connaître : un bit vaut 0 ou « non nul » ; les moniteurs comparent en booléens.
    `aff3ct.tools.hard(x)` (socket ou tableau) en donne la vue 0 / 1. Mesuré par `scripts/probe_bit_convention.py`
    → `docs/design/bit_convention.md` (à relancer à chaque évolution d'AFF3CT) : sur 100 combinaisons
    (fonction × type × implem × dtypes), les encodeurs rendent toujours 0 / 1, et seuls les décodeurs polaires
    **FAST** (SC, SCL, SCL_MEM, ASCL, ASCL_MEM) et **SCAN** rendent le bit de signe pour un 1 (`-128` en `int8`,
    `-2147483648` en `int32`), sur `V_K` comme sur `V_N` ; tous décodent correctement.
  - Défaut des surcharges tronquées corrigé : un argument suivant peut être donné sans les précédents
    (`encoder=` sans `crc=`), les défauts littéraux étant gardés.
  - **Interfaces des classes concrètes** ✅ : un module construit par une factory est typé d'après sa base wrappée la
    plus dérivée (`Decoder_SIHO_int32_float32`) ; plutôt que d'enregistrer chaque classe concrète (les factories les
    instancient avec des paramètres de template non exposés : `Decoder_polar_SC_fast_sys<B, Q, API_polar>`…), les
    accesseurs d'une interface sont liés sur les bases dont des enfants l'implémentent (d'après l'empreinte :
    `Encoder` → `frozen_bits`, `dynamic_frozen_bits`, `pretransform`, `trellis` ; `Decoder` → les trois premiers ;
    `Extractor` → `frozen_bits`) et atteignent l'interface par `dynamic_cast`
    (`internal/Common/Tools/interfaces.hpp`). Sur un module qui ne l'implémente pas, ils lèvent `AttributeError` :
    `hasattr(dec, "frozen_bits")` dit si le décodeur utilise des bits gelés.
  - **Templates appelables** ✅ : `af.tools.Sigma(0.5)`, `af.itl.Interleaver(core, D=spu.float32)` ; les mots-clés
    nommés comme les paramètres de template (ou `dtype=`) choisissent l'instance, les autres vont au constructeur.
  - **Modules header-only** (`module::Interleaver<D, T>`) : leurs combinaisons de dtypes viennent des builders qui les
    renvoient (`gen_instantiations.py`) ; builders `static` non `const` reconnus (`Interleaver::build`).
  - Vérifié : chaîne source → `enc.polar` → BPSK → AWGN → `dec.polar` (SC NAIVE/FAST, `int8`/`int16`/`int32`) →
    `mnt.bfer`, CA-SCL avec un CRC gardé en vie par le décodeur, SISO SCAN.
- Modules (via les fonctions générées ; vérifiés : polaire, LDPC, BCH, RS, répétition, RSC, BPSK, AWGN, BFER) :
  `Source_random_fast`, `CRC_polynomial/NO`, `Encoder_{NO,polar,polar_sys,LDPC,LDPC_from_H,BCH,RS,repetition_sys}`,
  `Modem_BPSK(_fast)`, `Channel_{AWGN_LLR,NO}`, `Quantizer_{NO,pow2}`, `Decoder_{NO,repetition,BCH_std,RS_std}` +
  polaire SC et LDPC BP via factory, `Interleaver`, `Puncturer_NO`, `Monitor_BFER`.
- Tools ✅ : `Sparse_matrix` (depuis/vers NumPy, `__array__`, `to_scipy` / `from_scipy`, `T`, `turn`…), `AList`, `QC`,
  `LDPC_matrix_handler` (`read` → `(H, info_bits_pos, pct_pattern)`, `transform_H_to_G`), `Galois`,
  `BCH_polynomial_generator`, `RS_polynomial_generator`, `Frozenbits_generator_{GA_Arikan,BEC,file}`
  (`gen.generate(noise)` → tableau de booléens), `Interleaver_core_*` (les 12 cœurs, tous les `T`) + module
  `aff3ct.itl.Interleaver`, `Sigma` + conversions (`ebn0_to_esn0`, `esn0_to_sigma`…, `sigma_from_ebn0`),
  `Reporter_{BFER,noise,throughput}` (avec `spu.Terminal_std`), module `Monitor_BFER` (compteurs `n_fe`, `ber`, `fer`…,
  `collect`, callbacks).
  Notes : dans AFF3CT, `sigma_to_esn0` n'est pas l'inverse de `esn0_to_sigma` (écart de 3,01 dB, facteur 2) ;
  `H` est stocké verticalement (N lignes, comme les fichiers AList), l'encodeur `type="LDPC_H"` calcule G lui-même
  et donne `info_bits_pos` au décodeur ; les tailles de `enc.rs` / `dec.rs` sont en symboles.
- Empreinte : `strip` des commentaires corrigé (un `//` dans un `/* … */`, ici une URL, masquait sa fin) : deux
  classes manquaient (`RS_polynomial_generator`, `Decoder_RS_std`).
- **Validation numérique** ✅ (`tests/test_references.py`, < 2 s) : polaire SC (128, 96) GA, BCH (127, 106) t = 3 et
  LDPC CCSDS (128, 64) BP SPA à 50 itérations, comparés aux références `lib/aff3ct/refs` (FER à 4 écarts-types
  binomiaux) ; la CI récupère `refs` et, de `conf`, la seule matrice utilisée.
- Exemple ✅ `examples/polar_bfer.py` (`streampu.Sequence` multi-thread, `Terminal_std`, bits gelés adaptés au bruit
  par `set_frozen_bits` sur les clones). Restent `examples/ldpc_bfer.py` et un notebook.
- Constaté côté pystreampu (à remonter) : `Terminal_std(reporters)` ne garde pas ses reporters en vie (à garder par
  l'appelant) ; `stop_temp_report` est lié à `start_temp_report` ; `Sequence(task)` prend la tâche pour la
  **première** (le passer par une socket de fin : `Sequence(mnt["check_errors::status"])`).
- **Réduction multi-thread** ✅ : avec `Monitor_BFER`, chaque thread a son clone et la séquence s'arrête dès qu'**un**
  clone atteint `max_fe` (FER réduit biaisé vers le haut ; l'original ne compte au mieux que les trames du premier
  thread).
  Classe propre à pyaff3ct, temporaire, d'après `Monitor_BFER_AR` de py_aff3ct :
  `internal/include/internal/Module/Monitor/BFER_AR/Monitor_BFER_AR.hpp` → `af.mnt.Monitor_BFER_AR(K, max_fe)`.
  Elle dérive de `Monitor_BFER<B>` (les reporters et accesseurs restent valables) ; ses clones partagent des totaux
  (mutex) recopiés dans le clone et dans l'original à chaque trame, `is_done()` relit les totaux, `reset()` les
  remet à zéro. Les classes de pyaff3ct sont déclarées dans `PYAFF3CT_TEMPLATES` (`_dispatch.py`) pour le
  regroupement par dtype. Vérifié : 4 threads → FE total = `max_fe` (+ trames en vol), FER conforme à la référence
  polaire. À retirer si AFF3CT / pystreampu offrent l'équivalent (`Monitor_reduction`).

### Phase 3 — Couverture cœur (priorité **P1**, 229 entrées)
- Toutes les familles restantes « mainstream » : Turbo/RSC (+ `Post_processing_SISO`, `Flip_and_check`, `Scaling_factor`),
  RA, Repetition, Conv/Viterbi, Polar SCL/ASCL/SCF/SCAN, LDPC (toutes les règles via factory), Modem générique
  (`Constellation_*`), OOK, Rayleigh, BEC/BSC, `Extractor_*`, `Puncturer_*`, `Quantizer_custom`, générateurs de bruit.
- `Codec_*` (via factories) : propriétés `encoder`, `decoder_siso`, `decoder_siho`, `extractor`, `puncturer`.
- **Codecs** ✅ (en cours de phase 3) : sous-module `aff3ct.codec`, une fonction par famille (`polar`, `ldpc`, `turbo`,
  `turbo_db`, `turbo_product`, `bch`, `rs`, `rsc`, `rsc_db`, `conv`, `ra`, `repetition`, `uncoded`, `polar_mk`,
  `polar_pac`, `polar_pt`) ; classes `Codec_*` (bases `Codec`, `Codec_HIHO/SIHO/SISO`) avec les modules en propriétés
  (`encoder`, `decoder_siho`, `decoder_siso`, `puncturer`, `extractor`, `interleaver` ; `None` si absent), qui gardent
  le codec en vie, et les accesseurs propres (`frozen_bits`, `trellis`, `H`, `GF`…).
  - Signature : `K`, `N_cw` et les arguments du builder (`crc`) positionnels ; `N` (taille de trame : une autre valeur
    que `N_cw` ajoute le poinçonneur) ; les paramètres des sous-factories **préfixés** par le nom de la
    sous-factory, comme les options de la ligne de commande (`dec_type`, `dec_L`, `enc_systematic`, `fbg_noise`,
    `pct_pattern`, `itl_core_type`…) ; les sous-factories sœurs de même préfixe CLI sont réglées ensemble
    (`enc_sub_standard` → `enc.sub1` et `enc.sub2`, comme `--enc-sub-std`) ; dtypes `B=`, `Q=`.
  - Les types dynamiques des sous-factories n'étant connus qu'à l'exécution, les fonctions sont construites à
    l'import (`aff3ct/codec.py`, depuis `CODECS` généré) : `inspect.signature` et `help()` les listent toutes.
    `af.codec.turbo.factory(...)` (mêmes arguments) rend la factory configurée (`headers()` comme le simulateur).
  - Les paramètres sont ceux des factories : une option CLI qui en règle plusieurs doit être traduite
    (`--dec-sf-type` → `dec_sf_enable=True, dec_sf_type=...`) ; `from_cli` reste disponible.
  - `cdc.set_noise(noise)` agit sur les modules du codec, pas sur leurs clones d'une `Sequence` multi-thread
    (bits gelés adaptatifs : `set_frozen_bits` sur les clones, comme `examples/polar_bfer.py`).
  - Générateur : factories templates à arguments par défaut liées (`Decoder_turbo<>`, `Encoder_turbo<>` : `dec_n_ite`,
    `dec_sub_*`, `dec_sf_*`…), leurs builders prenant les combinaisons du module renvoyé ; `enable_puncturer` lié.
  - Validé contre `refs` : RA (4096, 1024) MS 10 itérations et turbo LTE (K = 2048, CRC 24-LTEA, poinçonnage
    `11,10,01`, 8 itérations, facteur d'échelle LTE_VEC), à 4 threads ; `examples/ldpc_bfer.py` (codec LDPC).
- **Modems et canaux** ✅ : `Constellation_{PAM,PSK,QAM,user}` (`symbols` en tableau complexe, `bps`…) ;
  `af.mdm.modem(N, type="QAM", bps=4)` construit (et garde) la constellation des types génériques, comme le
  simulateur, et une constellation donnée fixe le type ; `af.mdm.modem(N, symbols=...)` pour une constellation
  quelconque sans objet ni fichier (constructeur protégé `Constellation(symbols, name)` d'AFF3CT, exposé par
  `af.tools.Constellation(symbols, normalize=True)` ; symbole `i` = image des bits de `i`, premier bit de poids
  faible) ; `mdm.N_mod` donne la taille du canal. Canaux AWGN,
  Rayleigh (`add_noise_wg` → `demodulate_wg`, `complex=True`), BEC et BSC (modem `OOK` avec `channel_type`, moniteur
  `count_unknown_values=True` comme le simulateur pour un bruit EP) validés contre `refs` (non codé : 16-QAM AWGN,
  QPSK Rayleigh, OOK BEC / BSC, BER à 5 écarts-types). Générateur : les templates d'outils header-only qui
  transmettent leurs paramètres à leur base en prennent les combinaisons (`Constellation_QAM<R>`).
- **Décodeurs et outils polaires** ✅ : `Polar_code` (mono / multi-noyaux), `Frozenbits_generator_{GA,RM,5G,TV}`,
  `Pretransform_generator(_file)`. `from_cli(args, strict=False)` : une ligne de commande AFF3CT complète donnée à
  chaque factory, qui n'en prend que ses arguments. `tests/test_references.py` reconstruit les chaînes **depuis la
  ligne de commande des références** (source, CRC, codec, modem, canal ; tailles propagées et AZCW comme
  `BFER_std.cpp`, poinçonneur activé comme les lanceurs polaire / turbo / LDPC) : CA-ASCL polaire raccourci,
  Viterbi, BCJR, répétition, LDPC BP flooding SPA / AMS (min, min*), layered NMS, Gallager A / B / E, WBF, MWBF,
  LDPC NMS sur BEC et BSC (bruit EP). La CI récupère les 4 matrices utilisées.
  Restent sans fonction : `Scaling_factor`, `Flip_and_check` (post-traitements internes aux décodeurs turbo, réglés
  par les codecs : `dec_sf_*`, `dec_fnc_*`).

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
2. **Deux copies statiques de StreamPU** (modèle officiel des extensions) : `set_task_autoalloc` refait à l'import.
   *Vérifié en phase 1* : traduction des exceptions, `Sequence` multi-thread (clones de modules AFF3CT) et typage des
   modules renvoyés par pystreampu (R8 bis, registre de downcasters, mergé dans pystreampu `develop`).
   Attention : réinstaller streampu touche les en-têtes StreamPU dont dépend AFF3CT, d'où une recompilation complète
   d'AFF3CT (~15 min sur 2 cœurs) au build suivant.
   Note : `Stateful` n'est pas exporté au niveau de `streampu` (seul `Stateful_core` l'est) : les tests utilisent
   `streampu._ext.sfl.Stateful` ; un export public côté pystreampu serait plus propre.
   Note : itérer sur une `streampu.Socket` (`for s in sock`, `list(sock)`) ne termine pas (`__getitem__` sans fin
   d'itération) — à corriger côté pystreampu (lever `IndexError` ou définir `__iter__`).
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
