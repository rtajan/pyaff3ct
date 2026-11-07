# Inventaire de wrapping

> Généré par `scripts/gen_class_graph.py`. La colonne *Statut* vient de `status.json` (clé `Kind::Name`, valeurs `todo` → `wip` → `done`) : c'est ce fichier qu'on édite, pas celui-ci.

| Espace | abstract | wrap | factory | func | skip |
|---|---|---|---|---|---|
| Module | 13 | 130 | 47 | 0 | 0 |
| Tools | 23 | 67 | 16 | 5 | 88 |
| Factory | 1 | 83 | 0 | 0 | 0 |

## Modules

| Classe | En-tête | Template | Bases | Stratégie | Priorité | Nom Python | Statut |
|---|---|---|---|---|---|---|---|
| `CRC` | `Module/CRC/CRC.hpp` | `typename B = int` | spu::module::Stateful | abstract | P0 | `aff3ct.crc.CRC` | done |
| `CRC_NO` | `Module/CRC/NO/CRC_NO.hpp` | `typename B = int` | CRC | wrap | P0 | `aff3ct.crc.no` | todo |
| `CRC_polynomial` | `Module/CRC/Polynomial/CRC_polynomial.hpp` | `typename B = int` | CRC | wrap | P0 | `aff3ct.crc.polynomial` | todo |
| `Channel_AWGN_LLR` | `Module/Channel/AWGN/Channel_AWGN_LLR.hpp` | `typename R = float` | Channel | wrap | P0 | `aff3ct.chn.awgn_llr` | todo |
| `Channel` | `Module/Channel/Channel.hpp` | `typename R = float` | spu::module::Stateful, spu::tools::Interface_set_seed | abstract | P0 | `aff3ct.chn.Channel` | done |
| `Channel_NO` | `Module/Channel/NO/Channel_NO.hpp` | `typename R = float` | Channel | wrap | P0 | `aff3ct.chn.no` | todo |
| `Coset` | `Module/Coset/Coset.hpp` | `typename B, typename D` | spu::module::Stateful | abstract | P0 | `aff3ct.cst.Coset` | done |
| `Decoder_BCH_std` | `Module/Decoder/BCH/Standard/Decoder_BCH_std.hpp` | `typename B = int, typename R = float` | Decoder_BCH | wrap | P0 | `aff3ct.dec.bch_std` | todo |
| `Decoder` | `Module/Decoder/Decoder.hpp` | `` | spu::module::Stateful, spu::tools::Interface_set_seed, spu::tools::Interface_reset | abstract | P0 | `aff3ct.dec.Decoder` | done |
| `Decoder_HIHO` | `Module/Decoder/Decoder_HIHO.hpp` | `typename B = int` | Decoder | abstract | P0 | `aff3ct.dec.Decoder_HIHO` | done |
| `Decoder_SIHO` | `Module/Decoder/Decoder_SIHO.hpp` | `typename B = int, typename R = float` | Decoder_HIHO | abstract | P0 | `aff3ct.dec.Decoder_SIHO` | done |
| `Decoder_SISO` | `Module/Decoder/Decoder_SISO.hpp` | `typename B = int, typename R = float` | Decoder_SIHO | abstract | P0 | `aff3ct.dec.Decoder_SISO` | done |
| `Decoder_LDPC_BP_flooding_SPA` | `Module/Decoder/LDPC/BP/Flooding/SPA/Decoder_LDPC_BP_flooding_SPA.hpp` | `typename B = int, typename R = float, class Syn…` | Decoder_LDPC_BP_flooding | factory | P0 | `aff3ct.dec.ldpc(…) [factory Decoder_LDPC]` | todo |
| `Decoder_LDPC_BP_horizontal_layered` | `Module/Decoder/LDPC/BP/Horizontal_layered/Decoder_LDPC_BP_horizontal_layered.hpp` | `typename B = int, typename R = float, class Upd…` | Decoder_SISO, Decoder_LDPC_BP | factory | P0 | `aff3ct.dec.ldpc(…) [factory Decoder_LDPC]` | todo |
| `Decoder_NO` | `Module/Decoder/NO/Decoder_NO.hpp` | `typename B = int, typename R = float` | Decoder_SISO | wrap | P0 | `aff3ct.dec.no` | todo |
| `Decoder_polar_SC_fast_sys` | `Module/Decoder/Polar/SC/Decoder_polar_SC_fast_sys.hpp` | `typename B = int, typename R = float, class API…` | Decoder_SIHO, tools::Interface_get_set_frozen_bits | factory | P0 | `aff3ct.dec.polar(…) [factory Decoder_polar]` | todo |
| `Decoder_polar_SC_naive` | `Module/Decoder/Polar/SC/Decoder_polar_SC_naive.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_SIHO, tools::Interface_get_set_frozen_bits | factory | P0 | `aff3ct.dec.polar(…) [factory Decoder_polar]` | todo |
| `Decoder_polar_SC_naive_sys` | `Module/Decoder/Polar/SC/Decoder_polar_SC_naive_sys.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_polar_SC_naive | factory | P0 | `aff3ct.dec.polar(…) [factory Decoder_polar]` | todo |
| `Decoder_RS_std` | `Module/Decoder/RS/Standard/Decoder_RS_std.hpp` | `typename B = int, typename R = float` | Decoder_RS | wrap | P0 | `aff3ct.dec.rs_std` | todo |
| `Decoder_repetition_fast` | `Module/Decoder/Repetition/Decoder_repetition_fast.hpp` | `typename B = int, typename R = float` | Decoder_repetition | wrap | P0 | `aff3ct.dec.repetition_fast` | todo |
| `Decoder_repetition_std` | `Module/Decoder/Repetition/Decoder_repetition_std.hpp` | `typename B = int, typename R = float` | Decoder_repetition | wrap | P0 | `aff3ct.dec.repetition_std` | todo |
| `Encoder_BCH` | `Module/Encoder/BCH/Encoder_BCH.hpp` | `typename B = int` | Encoder | wrap | P0 | `aff3ct.enc.bch` | todo |
| `Encoder` | `Module/Encoder/Encoder.hpp` | `typename B = int` | spu::module::Stateful, spu::tools::Interface_set_seed | abstract | P0 | `aff3ct.enc.Encoder` | done |
| `Encoder_LDPC` | `Module/Encoder/LDPC/Encoder_LDPC.hpp` | `typename B = int` | Encoder | wrap | P0 | `aff3ct.enc.ldpc` | todo |
| `Encoder_LDPC_from_H` | `Module/Encoder/LDPC/From_H/Encoder_LDPC_from_H.hpp` | `typename B = int` | Encoder_LDPC | wrap | P0 | `aff3ct.enc.ldpc_from_h` | todo |
| `Encoder_NO` | `Module/Encoder/NO/Encoder_NO.hpp` | `typename B = int` | Encoder | wrap | P0 | `aff3ct.enc.no` | todo |
| `Encoder_polar` | `Module/Encoder/Polar/Encoder_polar.hpp` | `typename B = int` | Encoder, tools::Interface_get_set_frozen_bits | wrap | P0 | `aff3ct.enc.polar` | todo |
| `Encoder_polar_sys` | `Module/Encoder/Polar/Encoder_polar_sys.hpp` | `typename B = int` | Encoder_polar | wrap | P0 | `aff3ct.enc.polar_sys` | todo |
| `Encoder_RS` | `Module/Encoder/RS/Encoder_RS.hpp` | `typename B = int` | Encoder | wrap | P0 | `aff3ct.enc.rs` | todo |
| `Encoder_repetition_sys` | `Module/Encoder/Repetition/Encoder_repetition_sys.hpp` | `typename B = int` | Encoder | wrap | P0 | `aff3ct.enc.repetition_sys` | todo |
| `Extractor` | `Module/Extractor/Extractor.hpp` | `typename B = int, typename Q = float` | spu::module::Stateful | abstract | P0 | `aff3ct.ext.Extractor` | done |
| `Interleaver` | `Module/Interleaver/Interleaver.hpp` | `typename D = int32_t, typename T = uint32_t` | spu::module::Stateful | wrap | P0 | `aff3ct.itl.interleaver` | done |
| `Modem_BPSK` | `Module/Modem/BPSK/Modem_BPSK.hpp` | `typename B = int, typename R = float, typename …` | Modem | wrap | P0 | `aff3ct.mdm.bpsk` | todo |
| `Modem_BPSK_fast` | `Module/Modem/BPSK/Modem_BPSK_fast.hpp` | `typename B = int, typename R = float, typename …` | Modem | wrap | P0 | `aff3ct.mdm.bpsk_fast` | todo |
| `Modem` | `Module/Modem/Modem.hpp` | `typename B = int, typename R = float, typename …` | spu::module::Stateful | abstract | P0 | `aff3ct.mdm.Modem` | done |
| `Monitor_BFER` | `Module/Monitor/BFER/Monitor_BFER.hpp` | `typename B = int` | Monitor | wrap | P0 | `aff3ct.mnt.bfer` | done |
| `Monitor` | `Module/Monitor/Monitor.hpp` | `` | spu::module::Stateful, spu::tools::Interface_reset, spu::tools::Interface_is_done | abstract | P0 | `aff3ct.mnt.Monitor` | done |
| `Puncturer_NO` | `Module/Puncturer/NO/Puncturer_NO.hpp` | `typename B = int, typename Q = float` | Puncturer | wrap | P0 | `aff3ct.pct.no` | todo |
| `Puncturer` | `Module/Puncturer/Puncturer.hpp` | `typename B = int, typename Q = float` | spu::module::Stateful | abstract | P0 | `aff3ct.pct.Puncturer` | done |
| `Quantizer_NO` | `Module/Quantizer/NO/Quantizer_NO.hpp` | `typename R = float, typename Q = int` | Quantizer | wrap | P0 | `aff3ct.qnt.no` | todo |
| `Quantizer_pow2` | `Module/Quantizer/Pow2/Quantizer_pow2.hpp` | `typename R = float, typename Q = float` | Quantizer | wrap | P0 | `aff3ct.qnt.pow2` | todo |
| `Quantizer` | `Module/Quantizer/Quantizer.hpp` | `typename R = float, typename Q = int` | spu::module::Stateful | abstract | P0 | `aff3ct.qnt.Quantizer` | done |
| `Source_random_fast` | `Module/Source/Random/Source_random_fast.hpp` | `typename B = int` | spu::module::Source | wrap | P0 | `aff3ct.src.random_fast` | todo |
| `CRC_polynomial_fast` | `Module/CRC/Polynomial/CRC_polynomial_fast.hpp` | `typename B = int` | CRC_polynomial | wrap | P1 | `aff3ct.crc.polynomial_fast` | todo |
| `CRC_polynomial_inter` | `Module/CRC/Polynomial/CRC_polynomial_inter.hpp` | `typename B = int` | CRC_polynomial | wrap | P1 | `aff3ct.crc.polynomial_inter` | todo |
| `Channel_binary_erasure` | `Module/Channel/Binary_erasure/Channel_binary_erasure.hpp` | `typename R = float` | Channel | wrap | P1 | `aff3ct.chn.binary_erasure` | todo |
| `Channel_binary_symmetric` | `Module/Channel/Binary_symmetric/Channel_binary_symmetric.hpp` | `typename R = float` | Channel | wrap | P1 | `aff3ct.chn.binary_symmetric` | todo |
| `Channel_Rayleigh_LLR` | `Module/Channel/Rayleigh/Channel_Rayleigh_LLR.hpp` | `typename R = float` | Channel | wrap | P1 | `aff3ct.chn.rayleigh_llr` | todo |
| `Decoder_BCH` | `Module/Decoder/BCH/Decoder_BCH.hpp` | `typename B = int, typename R = float` | Decoder_SIHO | wrap | P1 | `aff3ct.dec.bch` | todo |
| `Decoder_BCH_fast` | `Module/Decoder/BCH/Fast/Decoder_BCH_fast.hpp` | `typename B = int, typename R = float` | Decoder_BCH | wrap | P1 | `aff3ct.dec.bch_fast` | todo |
| `Decoder_Viterbi_SIHO` | `Module/Decoder/Conv/Viterbi/Decoder_Viterbi_SIHO.hpp` | `typename B = int, typename R = int` | Decoder_SIHO | wrap | P1 | `aff3ct.dec.viterbi_siho` | todo |
| `Decoder_chase_std` | `Module/Decoder/Generic/Chase/Decoder_chase_std.hpp` | `typename B = int, typename R = float` | Decoder_SIHO | wrap | P1 | `aff3ct.dec.chase_std` | todo |
| `Decoder_maximum_likelihood` | `Module/Decoder/Generic/ML/Decoder_maximum_likelihood.hpp` | `typename B = int, typename R = float` | Decoder_SIHO | wrap | P1 | `aff3ct.dec.maximum_likelihood` | todo |
| `Decoder_maximum_likelihood_naive` | `Module/Decoder/Generic/ML/Decoder_maximum_likelihood_naive.hpp` | `typename B = int, typename R = float` | Decoder_maximum_likelihood | wrap | P1 | `aff3ct.dec.maximum_likelihood_naive` | todo |
| `Decoder_maximum_likelihood_std` | `Module/Decoder/Generic/ML/Decoder_maximum_likelihood_std.hpp` | `typename B = int, typename R = float` | Decoder_maximum_likelihood | wrap | P1 | `aff3ct.dec.maximum_likelihood_std` | todo |
| `Decoder_LDPC_bit_flipping` | `Module/Decoder/LDPC/BF/Decoder_LDPC_bit_flipping.hpp` | `typename B = int, typename R = float` | Decoder_SISO | wrap | P1 | `aff3ct.dec.ldpc_bit_flipping` | todo |
| `Decoder_LDPC_bit_flipping_hard` | `Module/Decoder/LDPC/BF/Decoder_LDPC_bit_flipping_hard.hpp` | `typename B = int, typename R = float` | Decoder_SIHO | wrap | P1 | `aff3ct.dec.ldpc_bit_flipping_hard` | todo |
| `Decoder_LDPC_bit_flipping_OMWBF` | `Module/Decoder/LDPC/BF/OMWBF/Decoder_LDPC_bit_flipping_OMWBF.hpp` | `typename B = int, typename R = float` | Decoder_LDPC_bit_flipping | wrap | P1 | `aff3ct.dec.ldpc_bit_flipping_omwbf` | todo |
| `Decoder_LDPC_probabilistic_parallel_bit_flipping` | `Module/Decoder/LDPC/BF/PPBF/Decoder_LDPC_probabilistic_parallel_bit_flipping.hpp` | `typename B = int, typename R = float` | Decoder_LDPC_bit_flipping_hard | wrap | P1 | `aff3ct.dec.ldpc_probabilistic_parallel_bit_flipping` | todo |
| `Decoder_LDPC_BP` | `Module/Decoder/LDPC/BP/Decoder_LDPC_BP.hpp` | `` |  | wrap | P1 | `aff3ct.dec.ldpc_bp` | todo |
| `Decoder_LDPC_BP_flooding` | `Module/Decoder/LDPC/BP/Flooding/Decoder_LDPC_BP_flooding.hpp` | `typename B = int, typename R = float, class Upd…` | Decoder_SISO, Decoder_LDPC_BP | factory | P1 | `aff3ct.dec.ldpc(…) [factory Decoder_LDPC]` | todo |
| `Decoder_LDPC_BP_flooding_inter` | `Module/Decoder/LDPC/BP/Flooding/Decoder_LDPC_BP_flooding_inter.hpp` | `typename B = int, typename R = float, class Upd…` | Decoder_SISO, Decoder_LDPC_BP | factory | P1 | `aff3ct.dec.ldpc(…) [factory Decoder_LDPC]` | todo |
| `Decoder_LDPC_BP_flooding_Gallager_A` | `Module/Decoder/LDPC/BP/Flooding/Gallager/Decoder_LDPC_BP_flooding_Gallager_A.hpp` | `typename B = int, typename R = float` | Decoder_SIHO, Decoder_LDPC_BP | wrap | P1 | `aff3ct.dec.ldpc_bp_flooding_gallager_a` | todo |
| `Decoder_LDPC_BP_flooding_Gallager_B` | `Module/Decoder/LDPC/BP/Flooding/Gallager/Decoder_LDPC_BP_flooding_Gallager_B.hpp` | `typename B = int, typename R = float` | Decoder_LDPC_BP_flooding_Gallager_A | wrap | P1 | `aff3ct.dec.ldpc_bp_flooding_gallager_b` | todo |
| `Decoder_LDPC_BP_flooding_Gallager_E` | `Module/Decoder/LDPC/BP/Flooding/Gallager/Decoder_LDPC_BP_flooding_Gallager_E.hpp` | `typename B = int, typename R = float` | Decoder_LDPC_BP_flooding_Gallager_A | wrap | P1 | `aff3ct.dec.ldpc_bp_flooding_gallager_e` | todo |
| `Decoder_LDPC_BP_horizontal_layered_inter` | `Module/Decoder/LDPC/BP/Horizontal_layered/Decoder_LDPC_BP_horizontal_layered_inter.hpp` | `typename B = int, typename R = float, class Upd…` | Decoder_SISO, Decoder_LDPC_BP | factory | P1 | `aff3ct.dec.ldpc(…) [factory Decoder_LDPC]` | todo |
| `Decoder_LDPC_BP_horizontal_layered_ONMS_inter` | `Module/Decoder/LDPC/BP/Horizontal_layered/ONMS/Decoder_LDPC_BP_horizontal_layered_ONMS_inter.hpp` | `typename B = int, typename R = float` | Decoder_SISO, Decoder_LDPC_BP | wrap | P1 | `aff3ct.dec.ldpc_bp_horizontal_layered_onms_inter` | todo |
| `Decoder_LDPC_BP_peeling` | `Module/Decoder/LDPC/BP/Peeling/Decoder_LDPC_BP_peeling.hpp` | `typename B = int, typename R = float` | Decoder_SIHO, Decoder_LDPC_BP | wrap | P1 | `aff3ct.dec.ldpc_bp_peeling` | todo |
| `Decoder_LDPC_BP_vertical_layered` | `Module/Decoder/LDPC/BP/Vertical_layered/Decoder_LDPC_BP_vertical_layered.hpp` | `typename B = int, typename R = float, class Upd…` | Decoder_SISO, Decoder_LDPC_BP | factory | P1 | `aff3ct.dec.ldpc(…) [factory Decoder_LDPC]` | todo |
| `Decoder_LDPC_BP_vertical_layered_inter` | `Module/Decoder/LDPC/BP/Vertical_layered/Decoder_LDPC_BP_vertical_layered_inter.hpp` | `typename B = int, typename R = float, class Upd…` | Decoder_SISO, Decoder_LDPC_BP | factory | P1 | `aff3ct.dec.ldpc(…) [factory Decoder_LDPC]` | todo |
| `Decoder_polar_ASCL_MEM_fast_CA_sys` | `Module/Decoder/Polar/ASCL/Decoder_polar_ASCL_MEM_fast_CA_sys.hpp` | `typename B = int, typename R = float, class API…` | Decoder_polar_SCL_MEM_fast_CA_sys | factory | P1 | `aff3ct.dec.polar(…) [factory Decoder_polar]` | todo |
| `Decoder_polar_ASCL_fast_CA_sys` | `Module/Decoder/Polar/ASCL/Decoder_polar_ASCL_fast_CA_sys.hpp` | `typename B = int, typename R = float, class API…` | Decoder_polar_SCL_fast_CA_sys | factory | P1 | `aff3ct.dec.polar(…) [factory Decoder_polar]` | todo |
| `Decoder_polar_SCAN_naive` | `Module/Decoder/Polar/SCAN/Decoder_polar_SCAN_naive.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_SISO, tools::Interface_get_set_frozen_bits | factory | P1 | `aff3ct.dec.polar(…) [factory Decoder_polar]` | todo |
| `Decoder_polar_SCAN_naive_sys` | `Module/Decoder/Polar/SCAN/Decoder_polar_SCAN_naive_sys.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_polar_SCAN_naive | factory | P1 | `aff3ct.dec.polar(…) [factory Decoder_polar]` | todo |
| `Decoder_polar_SCF_naive` | `Module/Decoder/Polar/SCF/Decoder_polar_SCF_naive.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_polar_SC_naive | factory | P1 | `aff3ct.dec.polar(…) [factory Decoder_polar]` | todo |
| `Decoder_polar_SCF_naive_sys` | `Module/Decoder/Polar/SCF/Decoder_polar_SCF_naive_sys.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_polar_SCF_naive | factory | P1 | `aff3ct.dec.polar(…) [factory Decoder_polar]` | todo |
| `Decoder_polar_SCL_MEM_fast_CA_sys` | `Module/Decoder/Polar/SCL/CRC/Decoder_polar_SCL_MEM_fast_CA_sys.hpp` | `typename B = int, typename R = float, class API…` | Decoder_polar_SCL_MEM_fast_sys | factory | P1 | `aff3ct.dec.polar(…) [factory Decoder_polar]` | todo |
| `Decoder_polar_SCL_fast_CA_sys` | `Module/Decoder/Polar/SCL/CRC/Decoder_polar_SCL_fast_CA_sys.hpp` | `typename B = int, typename R = float, class API…` | Decoder_polar_SCL_fast_sys | factory | P1 | `aff3ct.dec.polar(…) [factory Decoder_polar]` | todo |
| `Decoder_polar_SCL_naive_CA` | `Module/Decoder/Polar/SCL/CRC/Decoder_polar_SCL_naive_CA.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_polar_SCL_naive | factory | P1 | `aff3ct.dec.polar(…) [factory Decoder_polar]` | todo |
| `Decoder_polar_SCL_naive_CA_sys` | `Module/Decoder/Polar/SCL/CRC/Decoder_polar_SCL_naive_CA_sys.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_polar_SCL_naive_CA | factory | P1 | `aff3ct.dec.polar(…) [factory Decoder_polar]` | todo |
| `Decoder_polar_SCL_MEM_fast_sys` | `Module/Decoder/Polar/SCL/Decoder_polar_SCL_MEM_fast_sys.hpp` | `typename B = int, typename R = float, class API…` | Decoder_SIHO, tools::Interface_get_set_frozen_bits | factory | P1 | `aff3ct.dec.polar(…) [factory Decoder_polar]` | todo |
| `Decoder_polar_SCL_fast_sys` | `Module/Decoder/Polar/SCL/Decoder_polar_SCL_fast_sys.hpp` | `typename B = int, typename R = float, class API…` | Decoder_SIHO, tools::Interface_get_set_frozen_bits | factory | P1 | `aff3ct.dec.polar(…) [factory Decoder_polar]` | todo |
| `Decoder_polar_SCL_naive` | `Module/Decoder/Polar/SCL/Decoder_polar_SCL_naive.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_SIHO, tools::Interface_get_set_frozen_bits | factory | P1 | `aff3ct.dec.polar(…) [factory Decoder_polar]` | todo |
| `Decoder_polar_SCL_naive_sys` | `Module/Decoder/Polar/SCL/Decoder_polar_SCL_naive_sys.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_polar_SCL_naive | factory | P1 | `aff3ct.dec.polar(…) [factory Decoder_polar]` | todo |
| `Decoder_RA` | `Module/Decoder/RA/Decoder_RA.hpp` | `typename B = int, typename R = float` | Decoder_SIHO | wrap | P1 | `aff3ct.dec.ra` | todo |
| `Decoder_RS` | `Module/Decoder/RS/Decoder_RS.hpp` | `typename B = int, typename R = float` | Decoder_SIHO | wrap | P1 | `aff3ct.dec.rs` | todo |
| `Decoder_RSC_BCJR` | `Module/Decoder/RSC/BCJR/Decoder_RSC_BCJR.hpp` | `typename B = int, typename R = float` | Decoder_SISO | wrap | P1 | `aff3ct.dec.rsc_bcjr` | todo |
| `Decoder_RSC_BCJR_inter` | `Module/Decoder/RSC/BCJR/Inter/Decoder_RSC_BCJR_inter.hpp` | `typename B = int, typename R = float` | Decoder_RSC_BCJR | wrap | P1 | `aff3ct.dec.rsc_bcjr_inter` | todo |
| `Decoder_RSC_BCJR_inter_fast` | `Module/Decoder/RSC/BCJR/Inter/Decoder_RSC_BCJR_inter_fast.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_RSC_BCJR_inter | factory | P1 | `aff3ct.dec.rsc(…) [factory Decoder_RSC]` | todo |
| `Decoder_RSC_BCJR_inter_std` | `Module/Decoder/RSC/BCJR/Inter/Decoder_RSC_BCJR_inter_std.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_RSC_BCJR_inter | factory | P1 | `aff3ct.dec.rsc(…) [factory Decoder_RSC]` | todo |
| `Decoder_RSC_BCJR_inter_very_fast` | `Module/Decoder/RSC/BCJR/Inter/Decoder_RSC_BCJR_inter_very_fast.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_RSC_BCJR_inter | factory | P1 | `aff3ct.dec.rsc(…) [factory Decoder_RSC]` | todo |
| `Decoder_RSC_BCJR_inter_intra` | `Module/Decoder/RSC/BCJR/Inter_intra/Decoder_RSC_BCJR_inter_intra.hpp` | `typename B = int, typename R = float` | Decoder_RSC_BCJR | wrap | P1 | `aff3ct.dec.rsc_bcjr_inter_intra` | todo |
| `Decoder_RSC_BCJR_intra` | `Module/Decoder/RSC/BCJR/Intra/Decoder_RSC_BCJR_intra.hpp` | `typename B = int, typename R = float` | Decoder_RSC_BCJR | wrap | P1 | `aff3ct.dec.rsc_bcjr_intra` | todo |
| `Decoder_RSC_BCJR_intra_fast` | `Module/Decoder/RSC/BCJR/Intra/Decoder_RSC_BCJR_intra_fast.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_RSC_BCJR_intra | factory | P1 | `aff3ct.dec.rsc(…) [factory Decoder_RSC]` | todo |
| `Decoder_RSC_BCJR_intra_std` | `Module/Decoder/RSC/BCJR/Intra/Decoder_RSC_BCJR_intra_std.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_RSC_BCJR_intra | factory | P1 | `aff3ct.dec.rsc(…) [factory Decoder_RSC]` | todo |
| `Decoder_RSC_BCJR_seq` | `Module/Decoder/RSC/BCJR/Seq/Decoder_RSC_BCJR_seq.hpp` | `typename B = int, typename R = float` | Decoder_RSC_BCJR | wrap | P1 | `aff3ct.dec.rsc_bcjr_seq` | todo |
| `Decoder_RSC_BCJR_seq_fast` | `Module/Decoder/RSC/BCJR/Seq/Decoder_RSC_BCJR_seq_fast.hpp` | `typename B = int, typename R = float, typename …` | Decoder_RSC_BCJR_seq | factory | P1 | `aff3ct.dec.rsc(…) [factory Decoder_RSC]` | todo |
| `Decoder_RSC_BCJR_seq_scan` | `Module/Decoder/RSC/BCJR/Seq/Decoder_RSC_BCJR_seq_scan.hpp` | `typename B = int, typename R = float, typename …` | Decoder_RSC_BCJR_seq | wrap | P1 | `aff3ct.dec.rsc_bcjr_seq_scan` | todo |
| `Decoder_RSC_BCJR_seq_std` | `Module/Decoder/RSC/BCJR/Seq/Decoder_RSC_BCJR_seq_std.hpp` | `typename B = int, typename R = float, typename …` | Decoder_RSC_BCJR_seq | factory | P1 | `aff3ct.dec.rsc(…) [factory Decoder_RSC]` | todo |
| `Decoder_RSC_BCJR_seq_very_fast` | `Module/Decoder/RSC/BCJR/Seq/Decoder_RSC_BCJR_seq_very_fast.hpp` | `typename B = int, typename R = float, typename …` | Decoder_RSC_BCJR_seq | factory | P1 | `aff3ct.dec.rsc(…) [factory Decoder_RSC]` | todo |
| `Decoder_RSC_BCJR_seq_generic` | `Module/Decoder/RSC/BCJR/Seq_generic/Decoder_RSC_BCJR_seq_generic.hpp` | `typename B = int, typename R = float` | Decoder_RSC_BCJR | wrap | P1 | `aff3ct.dec.rsc_bcjr_seq_generic` | todo |
| `Decoder_RSC_BCJR_seq_generic_std` | `Module/Decoder/RSC/BCJR/Seq_generic/Decoder_RSC_BCJR_seq_generic_std.hpp` | `typename B = int, typename R = float, typename …` | Decoder_RSC_BCJR_seq_generic | factory | P1 | `aff3ct.dec.rsc(…) [factory Decoder_RSC]` | todo |
| `Decoder_RSC_DB_BCJR` | `Module/Decoder/RSC_DB/BCJR/Decoder_RSC_DB_BCJR.hpp` | `typename B = int, typename R = float` | Decoder_SISO | wrap | P1 | `aff3ct.dec.rsc_db_bcjr` | todo |
| `Decoder_RSC_DB_BCJR_DVB_RCS1` | `Module/Decoder/RSC_DB/BCJR/Decoder_RSC_DB_BCJR_DVB_RCS1.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_RSC_DB_BCJR | factory | P1 | `aff3ct.dec.rsc_db(…) [factory Decoder_RSC_DB]` | todo |
| `Decoder_RSC_DB_BCJR_DVB_RCS2` | `Module/Decoder/RSC_DB/BCJR/Decoder_RSC_DB_BCJR_DVB_RCS2.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_RSC_DB_BCJR | factory | P1 | `aff3ct.dec.rsc_db(…) [factory Decoder_RSC_DB]` | todo |
| `Decoder_RSC_DB_BCJR_generic` | `Module/Decoder/RSC_DB/BCJR/Decoder_RSC_DB_BCJR_generic.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_RSC_DB_BCJR | factory | P1 | `aff3ct.dec.rsc_db(…) [factory Decoder_RSC_DB]` | todo |
| `Decoder_repetition` | `Module/Decoder/Repetition/Decoder_repetition.hpp` | `typename B = int, typename R = float` | Decoder_SISO | wrap | P1 | `aff3ct.dec.repetition` | todo |
| `Decoder_repetition_vote` | `Module/Decoder/Repetition/Decoder_repetition_vote.hpp` | `typename B = int, typename R = float` | Decoder_repetition | wrap | P1 | `aff3ct.dec.repetition_vote` | todo |
| `Decoder_turbo` | `Module/Decoder/Turbo/Decoder_turbo.hpp` | `typename B = int, typename R = float` | Decoder_SIHO | wrap | P1 | `aff3ct.dec.turbo` | todo |
| `Decoder_turbo_fast` | `Module/Decoder/Turbo/Decoder_turbo_fast.hpp` | `typename B = int, typename R = float` | Decoder_turbo | wrap | P1 | `aff3ct.dec.turbo_fast` | todo |
| `Decoder_turbo_std` | `Module/Decoder/Turbo/Decoder_turbo_std.hpp` | `typename B = int, typename R = float` | Decoder_turbo | wrap | P1 | `aff3ct.dec.turbo_std` | todo |
| `Decoder_turbo_DB` | `Module/Decoder/Turbo_DB/Decoder_turbo_DB.hpp` | `typename B = int, typename R = float` | Decoder_SIHO | wrap | P1 | `aff3ct.dec.turbo_db` | todo |
| `Encoder_BCH_inter` | `Module/Encoder/BCH/Encoder_BCH_inter.hpp` | `typename B = int` | Encoder_BCH | wrap | P1 | `aff3ct.enc.bch_inter` | todo |
| `Encoder_conv` | `Module/Encoder/Conv/Encoder_conv.hpp` | `typename B = int` | Encoder, tools::Interface_get_trellis | wrap | P1 | `aff3ct.enc.conv` | todo |
| `Encoder_LDPC_from_IRA` | `Module/Encoder/LDPC/From_IRA/Encoder_LDPC_from_IRA.hpp` | `typename B = int` | Encoder_LDPC | wrap | P1 | `aff3ct.enc.ldpc_from_ira` | todo |
| `Encoder_LDPC_from_QC` | `Module/Encoder/LDPC/From_QC/Encoder_LDPC_from_QC.hpp` | `typename B = int` | Encoder_LDPC | wrap | P1 | `aff3ct.enc.ldpc_from_qc` | todo |
| `Encoder_LDPC_QC` | `Module/Encoder/LDPC/QC/Encoder_LDPC_QC.hpp` | `typename B = int` | Encoder_LDPC | wrap | P1 | `aff3ct.enc.ldpc_qc` | todo |
| `Encoder_LDPC_QC_fast` | `Module/Encoder/LDPC/QC/Encoder_LDPC_QC_fast.hpp` | `typename B = int` | Encoder_LDPC_QC | wrap | P1 | `aff3ct.enc.ldpc_qc_fast` | todo |
| `Encoder_RA` | `Module/Encoder/RA/Encoder_RA.hpp` | `typename B = int` | Encoder | wrap | P1 | `aff3ct.enc.ra` | todo |
| `Encoder_RSC3_CPE_sys` | `Module/Encoder/RSC/Encoder_RSC3_CPE_sys.hpp` | `typename B = int` | Encoder_RSC_sys | wrap | P1 | `aff3ct.enc.rsc3_cpe_sys` | todo |
| `Encoder_RSC_generic_sys` | `Module/Encoder/RSC/Encoder_RSC_generic_sys.hpp` | `typename B = int` | Encoder_RSC_sys | wrap | P1 | `aff3ct.enc.rsc_generic_sys` | todo |
| `Encoder_RSC_sys` | `Module/Encoder/RSC/Encoder_RSC_sys.hpp` | `typename B = int` | Encoder, tools::Interface_get_trellis | wrap | P1 | `aff3ct.enc.rsc_sys` | todo |
| `Encoder_RSC_DB` | `Module/Encoder/RSC_DB/Encoder_RSC_DB.hpp` | `typename B = int` | Encoder, tools::Interface_get_trellis | wrap | P1 | `aff3ct.enc.rsc_db` | todo |
| `Encoder_turbo` | `Module/Encoder/Turbo/Encoder_turbo.hpp` | `typename B = int` | Encoder | wrap | P1 | `aff3ct.enc.turbo` | todo |
| `Encoder_turbo_legacy` | `Module/Encoder/Turbo/Encoder_turbo_legacy.hpp` | `typename B = int` | Encoder_turbo | wrap | P1 | `aff3ct.enc.turbo_legacy` | todo |
| `Encoder_turbo_DB` | `Module/Encoder/Turbo_DB/Encoder_turbo_DB.hpp` | `typename B = int` | Encoder | wrap | P1 | `aff3ct.enc.turbo_db` | todo |
| `Extractor_LDPC` | `Module/Extractor/LDPC/Extractor_LDPC.hpp` | `typename B = int, typename Q = float` | Extractor | wrap | P1 | `aff3ct.ext.ldpc` | todo |
| `Extractor_polar` | `Module/Extractor/Polar/Extractor_polar.hpp` | `typename B = int, typename Q = float` | Extractor, tools::Interface_get_set_frozen_bits | wrap | P1 | `aff3ct.ext.polar` | todo |
| `Extractor_RSC` | `Module/Extractor/RSC/Extractor_RSC.hpp` | `typename B = int, typename Q = float` | Extractor | wrap | P1 | `aff3ct.ext.rsc` | todo |
| `Extractor_uncoded` | `Module/Extractor/Uncoded/Extractor_uncoded.hpp` | `typename B = int, typename Q = float` | Extractor | wrap | P1 | `aff3ct.ext.uncoded` | todo |
| `Modem_generic` | `Module/Modem/Generic/Modem_generic.hpp` | `typename B = int, typename R = float, typename …` | Modem | factory | P1 | `aff3ct.mdm.generic(…) [factory Modem]` | todo |
| `Modem_generic_fast` | `Module/Modem/Generic/Modem_generic_fast.hpp` | `typename B = int, typename R = float, typename …` | Modem_generic | factory | P1 | `aff3ct.mdm.generic(…) [factory Modem]` | todo |
| `Modem_OOK` | `Module/Modem/OOK/Modem_OOK.hpp` | `typename B = int, typename R = float, typename …` | Modem | wrap | P1 | `aff3ct.mdm.ook` | todo |
| `Modem_OOK_AWGN` | `Module/Modem/OOK/Modem_OOK_AWGN.hpp` | `typename B = int, typename R = float, typename …` | Modem_OOK | wrap | P1 | `aff3ct.mdm.ook_awgn` | todo |
| `Modem_OOK_BEC` | `Module/Modem/OOK/Modem_OOK_BEC.hpp` | `typename B = int, typename R = float, typename …` | Modem_OOK | wrap | P1 | `aff3ct.mdm.ook_bec` | todo |
| `Modem_OOK_BSC` | `Module/Modem/OOK/Modem_OOK_BSC.hpp` | `typename B = int, typename R = float, typename …` | Modem_OOK | wrap | P1 | `aff3ct.mdm.ook_bsc` | todo |
| `Puncturer_5G` | `Module/Puncturer/LDPC/Puncturer_5G.hpp` | `typename B = int, typename Q = float` | Puncturer | wrap | P1 | `aff3ct.pct.5g` | todo |
| `Puncturer_LDPC` | `Module/Puncturer/LDPC/Puncturer_LDPC.hpp` | `typename B = int, typename Q = float` | Puncturer | wrap | P1 | `aff3ct.pct.ldpc` | todo |
| `Puncturer_polar_shortlast` | `Module/Puncturer/Polar/Puncturer_polar_shortlast.hpp` | `typename B = int, typename Q = float` | Puncturer | wrap | P1 | `aff3ct.pct.polar_shortlast` | todo |
| `Puncturer_turbo` | `Module/Puncturer/Turbo/Puncturer_turbo.hpp` | `typename B = int, typename Q = float` | Puncturer | wrap | P1 | `aff3ct.pct.turbo` | todo |
| `Puncturer_turbo_DB` | `Module/Puncturer/Turbo_DB/Puncturer_turbo_DB.hpp` | `typename B = int, typename Q = float` | Puncturer | wrap | P1 | `aff3ct.pct.turbo_db` | todo |
| `Quantizer_custom` | `Module/Quantizer/Custom/Quantizer_custom.hpp` | `typename R = float, typename Q = float` | Quantizer | wrap | P1 | `aff3ct.qnt.custom` | todo |
| `Quantizer_pow2_fast` | `Module/Quantizer/Pow2/Quantizer_pow2_fast.hpp` | `typename R = float, typename Q = short` | Quantizer | wrap | P1 | `aff3ct.qnt.pow2_fast` | todo |
| `Channel_optical` | `Module/Channel/Optical/Channel_optical.hpp` | `typename R = float` | Channel | wrap | P2 | `aff3ct.chn.optical` | todo |
| `Channel_Rayleigh_LLR_user` | `Module/Channel/Rayleigh/Channel_Rayleigh_LLR_user.hpp` | `typename R = float` | Channel | wrap | P2 | `aff3ct.chn.rayleigh_llr_user` | todo |
| `Channel_user` | `Module/Channel/User/Channel_user.hpp` | `typename R = float` | Channel | wrap | P2 | `aff3ct.chn.user` | todo |
| `Channel_user_add` | `Module/Channel/User/Channel_user_add.hpp` | `typename R = float` | Channel_user | wrap | P2 | `aff3ct.chn.user_add` | todo |
| `Channel_user_be` | `Module/Channel/User/Channel_user_be.hpp` | `typename R = float` | Channel_user | wrap | P2 | `aff3ct.chn.user_be` | todo |
| `Channel_user_bs` | `Module/Channel/User/Channel_user_bs.hpp` | `typename R = float` | Channel_user | wrap | P2 | `aff3ct.chn.user_bs` | todo |
| `Coset_bit` | `Module/Coset/Bit/Coset_bit.hpp` | `typename B = int, typename D = int` | Coset | wrap | P2 | `aff3ct.cst.bit` | todo |
| `Coset_real` | `Module/Coset/Real/Coset_real.hpp` | `typename B = int, typename D = float` | Coset | wrap | P2 | `aff3ct.cst.real` | todo |
| `Decoder_BCH_genius` | `Module/Decoder/BCH/Genius/Decoder_BCH_genius.hpp` | `typename B = int, typename R = float` | Decoder_BCH | wrap | P2 | `aff3ct.dec.bch_genius` | todo |
| `Decoder_Viterbi_list_parallel` | `Module/Decoder/Conv/Viterbi_list/Decoder_Viterbi_list_parallel.hpp` | `typename B, typename Q` | Decoder_SIHO | wrap | P2 | `aff3ct.dec.viterbi_list_parallel` | todo |
| `Decoder_polar_MK_ASCL_naive_CA` | `Module/Decoder/Polar_MK/ASCL/Decoder_polar_MK_ASCL_naive_CA.hpp` | `typename B = int, typename R = float` | Decoder_polar_MK_SCL_naive_CA | wrap | P2 | `aff3ct.dec.polar_mk_ascl_naive_ca` | todo |
| `Decoder_polar_MK_ASCL_naive_CA_sys` | `Module/Decoder/Polar_MK/ASCL/Decoder_polar_MK_ASCL_naive_CA_sys.hpp` | `typename B = int, typename R = float` | Decoder_polar_MK_SCL_naive_CA_sys | wrap | P2 | `aff3ct.dec.polar_mk_ascl_naive_ca_sys` | todo |
| `Decoder_polar_MK_SC_naive` | `Module/Decoder/Polar_MK/SC/Decoder_polar_MK_SC_naive.hpp` | `typename B = int, typename R = float` | Decoder_SIHO, tools::Interface_get_set_frozen_bits | wrap | P2 | `aff3ct.dec.polar_mk_sc_naive` | todo |
| `Decoder_polar_MK_SC_naive_sys` | `Module/Decoder/Polar_MK/SC/Decoder_polar_MK_SC_naive_sys.hpp` | `typename B = int, typename R = float` | Decoder_polar_MK_SC_naive | wrap | P2 | `aff3ct.dec.polar_mk_sc_naive_sys` | todo |
| `Decoder_polar_MK_SCL_naive_CA` | `Module/Decoder/Polar_MK/SCL/CRC/Decoder_polar_MK_SCL_naive_CA.hpp` | `typename B = int, typename R = float` | Decoder_polar_MK_SCL_naive | wrap | P2 | `aff3ct.dec.polar_mk_scl_naive_ca` | todo |
| `Decoder_polar_MK_SCL_naive_CA_sys` | `Module/Decoder/Polar_MK/SCL/CRC/Decoder_polar_MK_SCL_naive_CA_sys.hpp` | `typename B = int, typename R = float` | Decoder_polar_MK_SCL_naive_CA | wrap | P2 | `aff3ct.dec.polar_mk_scl_naive_ca_sys` | todo |
| `Decoder_polar_MK_SCL_naive` | `Module/Decoder/Polar_MK/SCL/Decoder_polar_MK_SCL_naive.hpp` | `typename B = int, typename R = float` | Decoder_SIHO, tools::Interface_get_set_frozen_bits | wrap | P2 | `aff3ct.dec.polar_mk_scl_naive` | todo |
| `Decoder_polar_MK_SCL_naive_sys` | `Module/Decoder/Polar_MK/SCL/Decoder_polar_MK_SCL_naive_sys.hpp` | `typename B = int, typename R = float` | Decoder_polar_MK_SCL_naive | wrap | P2 | `aff3ct.dec.polar_mk_scl_naive_sys` | todo |
| `Decoder_polar_PAC_Fano_naive` | `Module/Decoder/Polar_PAC/Fano/Decoder_polar_PAC_Fano_naive.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_SIHO, tools::Interface_get_set_frozen_bits | factory | P2 | `aff3ct.dec.polar_pac(…) [factory Decoder_polar_PAC]` | todo |
| `Decoder_polar_PAC_SCL_naive` | `Module/Decoder/Polar_PAC/SCL/Decoder_polar_PAC_SCL_naive.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_SIHO, tools::Interface_get_set_frozen_bits | factory | P2 | `aff3ct.dec.polar_pac(…) [factory Decoder_polar_PAC]` | todo |
| `Decoder_polar_PT_SCL_naive` | `Module/Decoder/Polar_PT/SCL/Decoder_polar_PT_SCL_naive.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_SIHO, tools::Interface_get_set_pretransform, tools::Interface_get_set_dynamic_frozen_bits, tools::Interface_get_set_frozen_bits | factory | P2 | `aff3ct.dec.polar_pt(…) [factory Decoder_polar_PT]` | todo |
| `Decoder_RS_genius` | `Module/Decoder/RS/Genius/Decoder_RS_genius.hpp` | `typename B = int, typename R = float` | Decoder_RS | wrap | P2 | `aff3ct.dec.rs_genius` | todo |
| `Decoder_RSC_BCJR_inter_intra_fast_x2_AVX` | `Module/Decoder/RSC/BCJR/Inter_intra/Decoder_RSC_BCJR_inter_intra_fast_x2_AVX.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_RSC_BCJR_inter_intra | factory | P2 | `aff3ct.dec.rsc(…) [factory Decoder_RSC]` | todo |
| `Decoder_RSC_BCJR_inter_intra_fast_x2_SSE` | `Module/Decoder/RSC/BCJR/Inter_intra/Decoder_RSC_BCJR_inter_intra_fast_x2_SSE.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_RSC_BCJR_inter_intra | factory | P2 | `aff3ct.dec.rsc(…) [factory Decoder_RSC]` | todo |
| `Decoder_RSC_BCJR_inter_intra_fast_x4_AVX` | `Module/Decoder/RSC/BCJR/Inter_intra/Decoder_RSC_BCJR_inter_intra_fast_x4_AVX.hpp` | `typename B = int, typename R = float, tools::pr…` | Decoder_RSC_BCJR_inter_intra | factory | P2 | `aff3ct.dec.rsc(…) [factory Decoder_RSC]` | todo |
| `Decoder_RSC_BCJR_seq_generic_std_json` | `Module/Decoder/RSC/BCJR/Seq_generic/Decoder_RSC_BCJR_seq_generic_std_json.hpp` | `typename B = int, typename R = float, typename …` | Decoder_RSC_BCJR_seq_generic_std | factory | P2 | `aff3ct.dec.rsc(…) [factory Decoder_RSC]` | todo |
| `Decoder_chase_pyndiah` | `Module/Decoder/Turbo_product/Chase_pyndiah/Decoder_chase_pyndiah.hpp` | `typename B = int, typename R = float` | Decoder_SISO | wrap | P2 | `aff3ct.dec.chase_pyndiah` | todo |
| `Decoder_chase_pyndiah_fast` | `Module/Decoder/Turbo_product/Chase_pyndiah/Decoder_chase_pyndiah_fast.hpp` | `typename B = int, typename R = float` | Decoder_chase_pyndiah | wrap | P2 | `aff3ct.dec.chase_pyndiah_fast` | todo |
| `Decoder_turbo_product` | `Module/Decoder/Turbo_product/Decoder_turbo_product.hpp` | `typename B = int, typename R = float` | Decoder_SISO | wrap | P2 | `aff3ct.dec.turbo_product` | todo |
| `Encoder_AZCW` | `Module/Encoder/AZCW/Encoder_AZCW.hpp` | `typename B = int` | Encoder | wrap | P2 | `aff3ct.enc.azcw` | todo |
| `Encoder_coset` | `Module/Encoder/Coset/Encoder_coset.hpp` | `typename B = int` | Encoder | wrap | P2 | `aff3ct.enc.coset` | todo |
| `Encoder_LDPC_DVBS2` | `Module/Encoder/LDPC/DVBS2/Encoder_LDPC_DVBS2.hpp` | `typename B = int` | Encoder_LDPC | wrap | P2 | `aff3ct.enc.ldpc_dvbs2` | todo |
| `Encoder_polar_bitpacked` | `Module/Encoder/Polar/Encoder_polar_bitpacked.hpp` | `typename B = int` | Encoder_polar | wrap | P2 | `aff3ct.enc.polar_bitpacked` | todo |
| `Encoder_polar_bitpacked_sys` | `Module/Encoder/Polar/Encoder_polar_bitpacked_sys.hpp` | `typename B = int` | Encoder_polar_bitpacked | wrap | P2 | `aff3ct.enc.polar_bitpacked_sys` | todo |
| `Encoder_polar_MK` | `Module/Encoder/Polar_MK/Encoder_polar_MK.hpp` | `typename B = int` | Encoder, tools::Interface_get_set_frozen_bits | wrap | P2 | `aff3ct.enc.polar_mk` | todo |
| `Encoder_polar_MK_sys` | `Module/Encoder/Polar_MK/Encoder_polar_MK_sys.hpp` | `typename B = int` | Encoder_polar_MK | wrap | P2 | `aff3ct.enc.polar_mk_sys` | todo |
| `Encoder_polar_PAC` | `Module/Encoder/Polar_PAC/Encoder_polar_PAC.hpp` | `typename B = int` | Encoder_polar | wrap | P2 | `aff3ct.enc.polar_pac` | todo |
| `Encoder_polar_PT` | `Module/Encoder/Polar_PT/Encoder_polar_PT.hpp` | `typename B = int` | Encoder_polar, tools::Interface_get_set_pretransform, tools::Interface_get_set_dynamic_frozen_bits | wrap | P2 | `aff3ct.enc.polar_pt` | todo |
| `Encoder_RSC_generic_json_sys` | `Module/Encoder/RSC/Encoder_RSC_generic_json_sys.hpp` | `typename B = int` | Encoder_RSC_generic_sys | wrap | P2 | `aff3ct.enc.rsc_generic_json_sys` | todo |
| `Encoder_turbo_product` | `Module/Encoder/Turbo_product/Encoder_turbo_product.hpp` | `typename B = int` | Encoder | wrap | P2 | `aff3ct.enc.turbo_product` | todo |
| `Encoder_user` | `Module/Encoder/User/Encoder_user.hpp` | `typename B = int` | Encoder | wrap | P2 | `aff3ct.enc.user` | todo |
| `Modem_CPM` | `Module/Modem/CPM/Modem_CPM.hpp` | `typename B = int, typename R = float, typename …` | Modem | factory | P2 | `aff3ct.mdm.generic(…) [factory Modem]` | todo |
| `Modem_OOK_optical` | `Module/Modem/OOK/Modem_OOK_optical.hpp` | `typename B = int, typename R = float, typename …` | Modem_OOK | wrap | P2 | `aff3ct.mdm.ook_optical` | todo |
| `Modem_OOK_optical_rop_estimate` | `Module/Modem/OOK/Modem_OOK_optical_rop_estimate.hpp` | `typename B = int, typename R = float, typename …` | Modem_OOK | wrap | P2 | `aff3ct.mdm.ook_optical_rop_estimate` | todo |
| `Modem_SCMA` | `Module/Modem/SCMA/Modem_SCMA.hpp` | `typename B = int, typename R = float, typename …` | Modem | factory | P2 | `aff3ct.mdm.generic(…) [factory Modem]` | todo |
| `Monitor_EXIT` | `Module/Monitor/EXIT/Monitor_EXIT.hpp` | `typename B = int, typename R = float` | Monitor | wrap | P2 | `aff3ct.mnt.exit` | todo |
| `Monitor_MI` | `Module/Monitor/MI/Monitor_MI.hpp` | `typename B = int, typename R = float` | Monitor | wrap | P2 | `aff3ct.mnt.mi` | todo |

## Tools

| Classe | En-tête | Template | Bases | Stratégie | Priorité | Nom Python | Statut |
|---|---|---|---|---|---|---|---|
| `Matrix` | `Tools/Algo/Matrix/Matrix.hpp` | `` |  | abstract | P0 | `aff3ct.tools.Matrix` | done |
| `Sparse_matrix` | `Tools/Algo/Matrix/Sparse_matrix/Sparse_matrix.hpp` | `` | Matrix | wrap | P0 | `aff3ct.tools.Sparse_matrix` | done |
| `BCH_polynomial_generator` | `Tools/Code/BCH/BCH_polynomial_generator.hpp` | `typename I = int` | Galois | wrap | P0 | `aff3ct.tools.BCH_polynomial_generator` | done |
| `Frozenbits_generator` | `Tools/Code/Polar/Frozenbits_generator/Frozenbits_generator.hpp` | `` | Interface_get_set_noise, spu::tools::Interface_clone | abstract | P0 | `aff3ct.tools.polar.Frozenbits_generator` | done |
| `Frozenbits_generator_BEC` | `Tools/Code/Polar/Frozenbits_generator/Frozenbits_generator_BEC.hpp` | `` | Frozenbits_generator | wrap | P0 | `aff3ct.tools.polar.Frozenbits_generator_BEC` | done |
| `Frozenbits_generator_GA_Arikan` | `Tools/Code/Polar/Frozenbits_generator/Frozenbits_generator_GA_Arikan.hpp` | `` | Frozenbits_generator | wrap | P0 | `aff3ct.tools.polar.Frozenbits_generator_GA_Arikan` | done |
| `Frozenbits_generator_file` | `Tools/Code/Polar/Frozenbits_generator/Frozenbits_generator_file.hpp` | `` | Frozenbits_generator | wrap | P0 | `aff3ct.tools.polar.Frozenbits_generator_file` | done |
| `RS_polynomial_generator` | `Tools/Code/RS/RS_polynomial_generator.hpp` | `` | Galois | wrap | P0 | `aff3ct.tools.RS_polynomial_generator` | done |
| `Interface_get_set_frozen_bits` | `Tools/Interface/Interface_get_set_frozen_bits.hpp` | `` |  | abstract | P0 | `aff3ct.interfaces.Interface_get_set_frozen_bits` | done |
| `Interface_get_set_noise` | `Tools/Interface/Interface_get_set_noise.hpp` | `` |  | abstract | P0 | `aff3ct.interfaces.Interface_get_set_noise` | done |
| `Interface_notify_noise_update` | `Tools/Interface/Interface_notify_noise_update.hpp` | `` |  | abstract | P0 | `aff3ct.interfaces.Interface_notify_noise_update` | done |
| `Interleaver_core` | `Tools/Interleaver/Interleaver_core.hpp` | `typename T = uint32_t` | spu::tools::Interface_set_seed, spu::tools::Interface_get_set_n_frames, spu::tools::Interface_clone | abstract | P0 | `aff3ct.tools.itl.Interleaver_core` | done |
| `Interleaver_core_LTE` | `Tools/Interleaver/LTE/Interleaver_core_LTE.hpp` | `typename T = uint32_t` | Interleaver_core | wrap | P0 | `aff3ct.tools.itl.Interleaver_core_LTE` | done |
| `Interleaver_core_NO` | `Tools/Interleaver/NO/Interleaver_core_NO.hpp` | `typename T = uint32_t` | Interleaver_core | wrap | P0 | `aff3ct.tools.itl.Interleaver_core_NO` | done |
| `Interleaver_core_random` | `Tools/Interleaver/Random/Interleaver_core_random.hpp` | `typename T = uint32_t` | Interleaver_core | wrap | P0 | `aff3ct.tools.itl.Interleaver_core_random` | done |
| `Interleaver_core_user` | `Tools/Interleaver/User/Interleaver_core_user.hpp` | `typename T = uint32_t` | Interleaver_core | wrap | P0 | `aff3ct.tools.itl.Interleaver_core_user` | done |
| `Galois` | `Tools/Math/Galois.hpp` | `typename I = int` |  | abstract | P0 | `aff3ct.tools.Galois` | done |
| `Noise` | `Tools/Noise/Noise.hpp` | `typename R = float` |  | abstract | P0 | `aff3ct.tools.Noise` | done |
| `Sigma` | `Tools/Noise/Sigma.hpp` | `typename R = float` | Noise | wrap | P0 | `aff3ct.tools.Sigma` | done |
| `Reporter_BFER` | `Tools/Reporter/BFER/Reporter_BFER.hpp` | `typename B = int32_t` | Reporter_monitor | wrap | P0 | `aff3ct.reporter.Reporter_BFER` | done |
| `Reporter_noise` | `Tools/Reporter/Noise/Reporter_noise.hpp` | `typename R = float` | spu::tools::Reporter | wrap | P0 | `aff3ct.reporter.Reporter_noise` | done |
| `Reporter_monitor` | `Tools/Reporter/Reporter_monitor.hpp` | `class M_t` | spu::tools::Reporter | abstract | P0 | `aff3ct.reporter.Reporter_monitor` | todo |
| `Reporter_throughput` | `Tools/Reporter/Throughput/Reporter_throughput.hpp` | `typename T = uint64_t` | spu::tools::Reporter | wrap | P0 | `aff3ct.reporter.Reporter_throughput` | done |
| `Draw_generator` | `Tools/Algo/Draw_generator/Draw_generator.hpp` | `typename R = float` | spu::tools::Interface_set_seed, spu::tools::Interface_clone | abstract | P1 | `aff3ct.tools.gen.Draw_generator` | todo |
| `Event_generator` | `Tools/Algo/Draw_generator/Event_generator/Event_generator.hpp` | `typename R = float, typename E = typename tools…` | Draw_generator | abstract | P1 | `aff3ct.tools.gen.Event_generator` | todo |
| `Event_generator_fast` | `Tools/Algo/Draw_generator/Event_generator/Fast/Event_generator_fast.hpp` | `typename R = float, typename E = typename tools…` | Event_generator | wrap | P1 | `aff3ct.tools.gen.Event_generator_fast` | todo |
| `Event_generator_std` | `Tools/Algo/Draw_generator/Event_generator/Standard/Event_generator_std.hpp` | `typename R = float, typename E = typename tools…` | Event_generator | wrap | P1 | `aff3ct.tools.gen.Event_generator_std` | todo |
| `Gaussian_noise_generator_fast` | `Tools/Algo/Draw_generator/Gaussian_noise_generator/Fast/Gaussian_noise_generator_fast.hpp` | `typename R = float` | Gaussian_noise_generator | wrap | P1 | `aff3ct.tools.gen.Gaussian_noise_generator_fast` | todo |
| `Gaussian_noise_generator` | `Tools/Algo/Draw_generator/Gaussian_noise_generator/Gaussian_noise_generator.hpp` | `typename R = float` | Draw_generator | abstract | P1 | `aff3ct.tools.gen.Gaussian_noise_generator` | todo |
| `Gaussian_noise_generator_std` | `Tools/Algo/Draw_generator/Gaussian_noise_generator/Standard/Gaussian_noise_generator_std.hpp` | `typename R = float` | Gaussian_noise_generator | wrap | P1 | `aff3ct.tools.gen.Gaussian_noise_generator_std` | todo |
| `User_pdf_noise_generator_fast` | `Tools/Algo/Draw_generator/User_pdf_noise_generator/Fast/User_pdf_noise_generator_fast.hpp` | `typename R = float` | User_pdf_noise_generator | wrap | P1 | `aff3ct.tools.gen.User_pdf_noise_generator_fast` | todo |
| `User_pdf_noise_generator_std` | `Tools/Algo/Draw_generator/User_pdf_noise_generator/Standard/User_pdf_noise_generator_std.hpp` | `typename R = float` | User_pdf_noise_generator | wrap | P1 | `aff3ct.tools.gen.User_pdf_noise_generator_std` | todo |
| `User_pdf_noise_generator` | `Tools/Algo/Draw_generator/User_pdf_noise_generator/User_pdf_noise_generator.hpp` | `typename R = float` | Draw_generator | abstract | P1 | `aff3ct.tools.gen.User_pdf_noise_generator` | todo |
| `Full_matrix` | `Tools/Algo/Matrix/Full_matrix/Full_matrix.hpp` | `typename T = int32_t` | Matrix, std::vector | wrap | P1 | `aff3ct.tools.Full_matrix` | todo |
| `AList` | `Tools/Code/LDPC/AList/AList.hpp` | `` |  | func | P1 | `aff3ct.tools.ldpc.AList` | done |
| `LDPC_matrix_handler` | `Tools/Code/LDPC/Matrix_handler/LDPC_matrix_handler.hpp` | `` |  | func | P1 | `aff3ct.tools.ldpc.LDPC_matrix_handler` | done |
| `QC` | `Tools/Code/LDPC/QC/QC.hpp` | `` |  | func | P1 | `aff3ct.tools.ldpc.QC` | done |
| `Frozenbits_generator_5G` | `Tools/Code/Polar/Frozenbits_generator/Frozenbits_generator_5G.hpp` | `` | Frozenbits_generator_file | wrap | P1 | `aff3ct.tools.polar.Frozenbits_generator_5G` | done |
| `Frozenbits_generator_GA` | `Tools/Code/Polar/Frozenbits_generator/Frozenbits_generator_GA.hpp` | `` | Frozenbits_generator | wrap | P1 | `aff3ct.tools.polar.Frozenbits_generator_GA` | done |
| `Frozenbits_generator_RM` | `Tools/Code/Polar/Frozenbits_generator/Frozenbits_generator_RM.hpp` | `` | Frozenbits_generator | wrap | P1 | `aff3ct.tools.polar.Frozenbits_generator_RM` | done |
| `Frozenbits_generator_TV` | `Tools/Code/Polar/Frozenbits_generator/Frozenbits_generator_TV.hpp` | `` | Frozenbits_generator_file | wrap | P1 | `aff3ct.tools.polar.Frozenbits_generator_TV` | done |
| `Polar_code` | `Tools/Code/Polar/Polar_code.hpp` | `` |  | wrap | P1 | `aff3ct.tools.polar.Polar_code` | done |
| `Pretransform_generator` | `Tools/Code/Polar/Pretransform_generator/Pretransform_generator.hpp` | `` | Interface_get_set_noise, spu::tools::Interface_clone | abstract | P1 | `aff3ct.tools.polar.Pretransform_generator` | done |
| `Pretransform_generator_file` | `Tools/Code/Polar/Pretransform_generator/Pretransform_generator_file.hpp` | `` | Pretransform_generator | wrap | P1 | `aff3ct.tools.polar.Pretransform_generator_file` | done |
| `CRC_checker` | `Tools/Code/Turbo/Post_processing_SISO/CRC/CRC_checker.hpp` | `typename B = int, typename R = float` | Post_processing_SISO | wrap | P1 | `aff3ct.tools.turbo.CRC_checker` | todo |
| `CRC_checker_DB` | `Tools/Code/Turbo/Post_processing_SISO/CRC/CRC_checker_DB.hpp` | `typename B = int, typename R = float` | CRC_checker | wrap | P1 | `aff3ct.tools.turbo.CRC_checker_DB` | todo |
| `Flip_and_check` | `Tools/Code/Turbo/Post_processing_SISO/Flip_and_check/Flip_and_check.hpp` | `typename B = int, typename R = float` | CRC_checker | wrap | P1 | `aff3ct.tools.turbo.Flip_and_check` | todo |
| `Flip_and_check_DB` | `Tools/Code/Turbo/Post_processing_SISO/Flip_and_check/Flip_and_check_DB.hpp` | `typename B = int, typename R = float` | CRC_checker_DB | wrap | P1 | `aff3ct.tools.turbo.Flip_and_check_DB` | todo |
| `Post_processing_SISO` | `Tools/Code/Turbo/Post_processing_SISO/Post_processing_SISO.hpp` | `typename B = int, typename R = float` | spu::tools::Interface_clone, spu::tools::Interface_get_set_n_frames | abstract | P1 | `aff3ct.tools.turbo.Post_processing_SISO` | todo |
| `Scaling_factor` | `Tools/Code/Turbo/Post_processing_SISO/Scaling_factor/Scaling_factor.hpp` | `typename B = int, typename R = float` | Post_processing_SISO | wrap | P1 | `aff3ct.tools.turbo.Scaling_factor` | todo |
| `Scaling_factor_adaptive` | `Tools/Code/Turbo/Post_processing_SISO/Scaling_factor/Scaling_factor_adaptive.hpp` | `typename B = int, typename R = float` | Scaling_factor | wrap | P1 | `aff3ct.tools.turbo.Scaling_factor_adaptive` | todo |
| `Scaling_factor_array` | `Tools/Code/Turbo/Post_processing_SISO/Scaling_factor/Scaling_factor_array.hpp` | `typename B = int, typename R = float` | Scaling_factor | wrap | P1 | `aff3ct.tools.turbo.Scaling_factor_array` | todo |
| `Scaling_factor_constant` | `Tools/Code/Turbo/Post_processing_SISO/Scaling_factor/Scaling_factor_constant.hpp` | `typename B = int, typename R = float` | Scaling_factor | wrap | P1 | `aff3ct.tools.turbo.Scaling_factor_constant` | todo |
| `Scaling_factor_seq` | `Tools/Code/Turbo/Post_processing_SISO/Scaling_factor/Scaling_factor_seq.hpp` | `typename B = int, typename R = float` | Scaling_factor | wrap | P1 | `aff3ct.tools.turbo.Scaling_factor_seq` | todo |
| `Scaling_factor_vec` | `Tools/Code/Turbo/Post_processing_SISO/Scaling_factor/Scaling_factor_vec.hpp` | `typename B = int, typename R = float` | Scaling_factor | wrap | P1 | `aff3ct.tools.turbo.Scaling_factor_vec` | todo |
| `Self_corrected` | `Tools/Code/Turbo/Post_processing_SISO/Self_corrected/Self_corrected.hpp` | `typename B = int, typename R = float` | Post_processing_SISO | wrap | P1 | `aff3ct.tools.turbo.Self_corrected` | todo |
| `Codec_BCH` | `Tools/Codec/BCH/Codec_BCH.hpp` | `typename B = int, typename Q = float` | Codec_SIHO | factory | P1 | `aff3ct.codec.Codec_BCH` | done |
| `Codec` | `Tools/Codec/Codec.hpp` | `typename B = int, typename Q = float` | Interface_get_set_noise, Interface_notify_noise_update, spu::tools::Interface_get_set_n_frames, spu::tools::Interface_clone | abstract | P1 | `aff3ct.codec.Codec` | done |
| `Codec_HIHO` | `Tools/Codec/Codec_HIHO.hpp` | `typename B = int, typename Q = float` | Codec | abstract | P1 | `aff3ct.codec.Codec_HIHO` | done |
| `Codec_SIHO` | `Tools/Codec/Codec_SIHO.hpp` | `typename B = int, typename Q = float` | Codec_HIHO | abstract | P1 | `aff3ct.codec.Codec_SIHO` | done |
| `Codec_SISO` | `Tools/Codec/Codec_SISO.hpp` | `typename B = int, typename Q = float` | Codec_SIHO | abstract | P1 | `aff3ct.codec.Codec_SISO` | done |
| `Codec_conv` | `Tools/Codec/Conv/Codec_conv.hpp` | `typename B = int, typename Q = float` | Codec_SIHO | factory | P1 | `aff3ct.codec.Codec_conv` | done |
| `Codec_LDPC` | `Tools/Codec/LDPC/Codec_LDPC.hpp` | `typename B = int, typename Q = float` | Codec_SISO | factory | P1 | `aff3ct.codec.Codec_LDPC` | done |
| `Codec_polar` | `Tools/Codec/Polar/Codec_polar.hpp` | `typename B = int, typename Q = float` | Codec_SISO, Interface_get_set_frozen_bits | factory | P1 | `aff3ct.codec.Codec_polar` | done |
| `Codec_polar_MK` | `Tools/Codec/Polar_MK/Codec_polar_MK.hpp` | `typename B = int, typename Q = float` | Codec_SIHO, Interface_get_set_frozen_bits | factory | P1 | `aff3ct.codec.Codec_polar_MK` | done |
| `Codec_polar_PAC` | `Tools/Codec/Polar_PAC/Codec_polar_PAC.hpp` | `typename B = int, typename Q = float` | Codec_SISO, Interface_get_set_frozen_bits | factory | P1 | `aff3ct.codec.Codec_polar_PAC` | done |
| `Codec_polar_PT` | `Tools/Codec/Polar_PT/Codec_polar_PT.hpp` | `typename B = int, typename Q = float` | Codec_SISO, Interface_get_set_pretransform, Interface_get_set_frozen_bits, Interface_get_set_dynamic_frozen_bits | factory | P1 | `aff3ct.codec.Codec_polar_PT` | done |
| `Codec_RA` | `Tools/Codec/RA/Codec_RA.hpp` | `typename B = int, typename Q = float` | Codec_SIHO | factory | P1 | `aff3ct.codec.Codec_RA` | done |
| `Codec_RS` | `Tools/Codec/RS/Codec_RS.hpp` | `typename B = int, typename Q = float` | Codec_SIHO | factory | P1 | `aff3ct.codec.Codec_RS` | done |
| `Codec_RSC` | `Tools/Codec/RSC/Codec_RSC.hpp` | `typename B = int, typename Q = float` | Codec_SISO | factory | P1 | `aff3ct.codec.Codec_RSC` | done |
| `Codec_RSC_DB` | `Tools/Codec/RSC_DB/Codec_RSC_DB.hpp` | `typename B = int, typename Q = float` | Codec_SISO | factory | P1 | `aff3ct.codec.Codec_RSC_DB` | done |
| `Codec_repetition` | `Tools/Codec/Repetition/Codec_repetition.hpp` | `typename B = int, typename Q = float` | Codec_SIHO | factory | P1 | `aff3ct.codec.Codec_repetition` | done |
| `Codec_turbo` | `Tools/Codec/Turbo/Codec_turbo.hpp` | `typename B = int, typename Q = float` | Codec_SIHO | factory | P1 | `aff3ct.codec.Codec_turbo` | done |
| `Codec_turbo_DB` | `Tools/Codec/Turbo_DB/Codec_turbo_DB.hpp` | `typename B = int, typename Q = float` | Codec_SIHO | factory | P1 | `aff3ct.codec.Codec_turbo_DB` | done |
| `Codec_turbo_product` | `Tools/Codec/Turbo_product/Codec_turbo_product.hpp` | `typename B = int, typename Q = float` | Codec_SISO | factory | P1 | `aff3ct.codec.Codec_turbo_product` | done |
| `Codec_uncoded` | `Tools/Codec/Uncoded/Codec_uncoded.hpp` | `typename B = int, typename Q = float` | Codec_SISO | factory | P1 | `aff3ct.codec.Codec_uncoded` | done |
| `Constellation` | `Tools/Constellation/Constellation.hpp` | `typename R = float` |  | abstract | P1 | `aff3ct.tools.cst.Constellation` | done |
| `Constellation_PAM` | `Tools/Constellation/PAM/Constellation_PAM.hpp` | `typename R = float` | Constellation | wrap | P1 | `aff3ct.tools.cst.Constellation_PAM` | done |
| `Constellation_PSK` | `Tools/Constellation/PSK/Constellation_PSK.hpp` | `typename R = float` | Constellation | wrap | P1 | `aff3ct.tools.cst.Constellation_PSK` | done |
| `Constellation_QAM` | `Tools/Constellation/QAM/Constellation_QAM.hpp` | `typename R = float` | Constellation | wrap | P1 | `aff3ct.tools.cst.Constellation_QAM` | done |
| `Constellation_user` | `Tools/Constellation/User/Constellation_user.hpp` | `typename R = float` | Constellation | wrap | P1 | `aff3ct.tools.cst.Constellation_user` | done |
| `Command_parser` | `Tools/Factory/Command_parser.hpp` | `` |  | func | P1 | `aff3ct.factory.Command_parser` | todo |
| `Header` | `Tools/Factory/Header.hpp` | `` |  | func | P1 | `aff3ct.factory.Header` | todo |
| `Interface_get_set_dynamic_frozen_bits` | `Tools/Interface/Interface_get_set_dynamic_frozen_bits.hpp` | `` |  | abstract | P1 | `aff3ct.interfaces.Interface_get_set_dynamic_frozen_bits` | done |
| `Interface_get_set_pretransform` | `Tools/Interface/Interface_get_set_pretransform.hpp` | `` |  | abstract | P1 | `aff3ct.interfaces.Interface_get_set_pretransform` | done |
| `Interface_get_trellis` | `Tools/Interface/Interface_get_trellis.hpp` | `` |  | abstract | P1 | `aff3ct.interfaces.Interface_get_trellis` | done |
| `Interleaver_core_ARP_DVB_RCS1` | `Tools/Interleaver/ARP/Interleaver_core_ARP_DVB_RCS1.hpp` | `typename T = uint32_t` | Interleaver_core | wrap | P1 | `aff3ct.tools.itl.Interleaver_core_ARP_DVB_RCS1` | done |
| `Interleaver_core_ARP_DVB_RCS2` | `Tools/Interleaver/ARP/Interleaver_core_ARP_DVB_RCS2.hpp` | `typename T = uint32_t` | Interleaver_core | wrap | P1 | `aff3ct.tools.itl.Interleaver_core_ARP_DVB_RCS2` | done |
| `Interleaver_core_CCSDS` | `Tools/Interleaver/CCSDS/Interleaver_core_CCSDS.hpp` | `typename T = uint32_t` | Interleaver_core | wrap | P1 | `aff3ct.tools.itl.Interleaver_core_CCSDS` | done |
| `Interleaver_core_column_row` | `Tools/Interleaver/Column_row/Interleaver_core_column_row.hpp` | `typename T = uint32_t` | Interleaver_core | wrap | P1 | `aff3ct.tools.itl.Interleaver_core_column_row` | done |
| `Interleaver_core_golden` | `Tools/Interleaver/Golden/Interleaver_core_golden.hpp` | `typename T = uint32_t` | Interleaver_core | wrap | P1 | `aff3ct.tools.itl.Interleaver_core_golden` | done |
| `Interleaver_core_random_column` | `Tools/Interleaver/Random_column/Interleaver_core_random_column.hpp` | `typename T = uint32_t` | Interleaver_core | wrap | P1 | `aff3ct.tools.itl.Interleaver_core_random_column` | done |
| `Interleaver_core_row_column` | `Tools/Interleaver/Row_column/Interleaver_core_row_column.hpp` | `typename T = uint32_t` | Interleaver_core | wrap | P1 | `aff3ct.tools.itl.Interleaver_core_row_column` | done |
| `Distribution` | `Tools/Math/Distribution/Distribution.hpp` | `typename R = float` |  | wrap | P1 | `aff3ct.tools.Distribution` | todo |
| `Distributions` | `Tools/Math/Distribution/Distributions.hpp` | `typename R = float` |  | wrap | P1 | `aff3ct.tools.Distributions` | todo |
| `Event_probability` | `Tools/Noise/Event_probability.hpp` | `typename R = float` | Noise | wrap | P1 | `aff3ct.tools.Event_probability` | done |
| `Received_optical_power` | `Tools/Noise/Received_optical_power.hpp` | `typename R = float` | Noise | wrap | P1 | `aff3ct.tools.Received_optical_power` | done |
| `Monitor_reduction` | `Tools/Monitor/Monitor_reduction.hpp` | `class M` | Monitor_reduction_static, M | wrap | P2 | `aff3ct.tools.Monitor_reduction` | todo |
| `Monitor_reduction_static` | `Tools/Monitor/Monitor_reduction.hpp` | `` |  | wrap | P2 | `aff3ct.tools.Monitor_reduction_static` | todo |
| `Reporter_EXIT` | `Tools/Reporter/EXIT/Reporter_EXIT.hpp` | `typename B = int32_t, typename R = float` | Reporter_monitor | wrap | P2 | `aff3ct.reporter.Reporter_EXIT` | todo |
| `Reporter_MI` | `Tools/Reporter/MI/Reporter_MI.hpp` | `typename B = int32_t, typename R = float` | Reporter_monitor | wrap | P2 | `aff3ct.reporter.Reporter_MI` | todo |
| `Event_generator_GSL` | `Tools/Algo/Draw_generator/Event_generator/GSL/Event_generator_GSL.hpp` | `typename R = float, typename E = typename tools…` | Event_generator | wrap | P3 | `aff3ct.tools.gen.Event_generator_GSL` | todo |
| `Event_generator_MKL` | `Tools/Algo/Draw_generator/Event_generator/MKL/Event_generator_MKL.hpp` | `typename R = float, typename E = typename tools…` | Event_generator | wrap | P3 | `aff3ct.tools.gen.Event_generator_MKL` | todo |
| `Gaussian_noise_generator_GSL` | `Tools/Algo/Draw_generator/Gaussian_noise_generator/GSL/Gaussian_noise_generator_GSL.hpp` | `typename R = float` | Gaussian_noise_generator | wrap | P3 | `aff3ct.tools.gen.Gaussian_noise_generator_GSL` | todo |
| `Gaussian_noise_generator_MKL` | `Tools/Algo/Draw_generator/Gaussian_noise_generator/MKL/Gaussian_noise_generator_MKL.hpp` | `typename R = float` | Gaussian_noise_generator | wrap | P3 | `aff3ct.tools.gen.Gaussian_noise_generator_MKL` | todo |
| `User_pdf_noise_generator_GSL` | `Tools/Algo/Draw_generator/User_pdf_noise_generator/GSL/User_pdf_noise_generator_GSL.hpp` | `typename R = float` | User_pdf_noise_generator | wrap | P3 | `aff3ct.tools.gen.User_pdf_noise_generator_GSL` | todo |
| `User_pdf_noise_generator_MKL` | `Tools/Algo/Draw_generator/User_pdf_noise_generator/MKL/User_pdf_noise_generator_MKL.hpp` | `typename R = float` | User_pdf_noise_generator | wrap | P3 | `aff3ct.tools.gen.User_pdf_noise_generator_MKL` | todo |
| `Histogram` | `Tools/Algo/Histogram.hpp` | `typename R` | spu::tools::Interface_reset | wrap | P3 | `aff3ct.tools.Histogram` | todo |
| `Dumper` | `Tools/Display/Dumper/Dumper.hpp` | `` |  | wrap | P3 | `aff3ct.tools.Dumper` | todo |
| `Dumper_reduction` | `Tools/Display/Dumper/Dumper_reduction.hpp` | `` | Dumper | wrap | P3 | `aff3ct.tools.Dumper_reduction` | todo |
| `Frame_trace` | `Tools/Display/Frame_trace/Frame_trace.hpp` | `typename B = int` |  | wrap | P3 | `aff3ct.tools.Frame_trace` | todo |

## Factories

| Classe | En-tête | Template | Bases | Stratégie | Priorité | Nom Python | Statut |
|---|---|---|---|---|---|---|---|
| `Factory` | `Factory/Factory.hpp` | `` | spu::tools::Interface_clone | abstract | P0 | `(interne) aff3ct.factory.Factory` | done |
| `CRC` | `Factory/Module/CRC/CRC.hpp` | `` | Factory | wrap | P0 | `(interne) aff3ct.factory.CRC` | done |
| `Channel` | `Factory/Module/Channel/Channel.hpp` | `` | Factory | wrap | P0 | `(interne) aff3ct.factory.Channel` | done |
| `Decoder_BCH` | `Factory/Module/Decoder/BCH/Decoder_BCH.hpp` | `` | Decoder | wrap | P0 | `(interne) aff3ct.factory.Decoder_BCH` | done |
| `Decoder` | `Factory/Module/Decoder/Decoder.hpp` | `` | Factory | wrap | P0 | `(interne) aff3ct.factory.Decoder` | done |
| `Decoder_LDPC` | `Factory/Module/Decoder/LDPC/Decoder_LDPC.hpp` | `` | Decoder | wrap | P0 | `(interne) aff3ct.factory.Decoder_LDPC` | done |
| `Decoder_NO` | `Factory/Module/Decoder/NO/Decoder_NO.hpp` | `` | Decoder | wrap | P0 | `(interne) aff3ct.factory.Decoder_NO` | done |
| `Decoder_polar` | `Factory/Module/Decoder/Polar/Decoder_polar.hpp` | `` | Decoder | wrap | P0 | `(interne) aff3ct.factory.Decoder_polar` | done |
| `Decoder_RS` | `Factory/Module/Decoder/RS/Decoder_RS.hpp` | `` | Decoder | wrap | P0 | `(interne) aff3ct.factory.Decoder_RS` | done |
| `Decoder_repetition` | `Factory/Module/Decoder/Repetition/Decoder_repetition.hpp` | `` | Decoder | wrap | P0 | `(interne) aff3ct.factory.Decoder_repetition` | done |
| `Encoder_BCH` | `Factory/Module/Encoder/BCH/Encoder_BCH.hpp` | `` | Encoder | wrap | P0 | `(interne) aff3ct.factory.Encoder_BCH` | done |
| `Encoder` | `Factory/Module/Encoder/Encoder.hpp` | `` | Factory | wrap | P0 | `(interne) aff3ct.factory.Encoder` | done |
| `Encoder_LDPC` | `Factory/Module/Encoder/LDPC/Encoder_LDPC.hpp` | `` | Encoder | wrap | P0 | `(interne) aff3ct.factory.Encoder_LDPC` | done |
| `Encoder_NO` | `Factory/Module/Encoder/NO/Encoder_NO.hpp` | `` | Encoder | wrap | P0 | `(interne) aff3ct.factory.Encoder_NO` | done |
| `Encoder_polar` | `Factory/Module/Encoder/Polar/Encoder_polar.hpp` | `` | Encoder | wrap | P0 | `(interne) aff3ct.factory.Encoder_polar` | done |
| `Encoder_RS` | `Factory/Module/Encoder/RS/Encoder_RS.hpp` | `` | Encoder | wrap | P0 | `(interne) aff3ct.factory.Encoder_RS` | done |
| `Encoder_repetition` | `Factory/Module/Encoder/Repetition/Encoder_repetition.hpp` | `` | Encoder | wrap | P0 | `(interne) aff3ct.factory.Encoder_repetition` | done |
| `Interleaver` | `Factory/Module/Interleaver/Interleaver.hpp` | `` | Factory | wrap | P0 | `(interne) aff3ct.factory.Interleaver` | done |
| `Modem` | `Factory/Module/Modem/Modem.hpp` | `` | Factory | wrap | P0 | `(interne) aff3ct.factory.Modem` | done |
| `Monitor_BFER` | `Factory/Module/Monitor/BFER/Monitor_BFER.hpp` | `` | Monitor | wrap | P0 | `(interne) aff3ct.factory.Monitor_BFER` | done |
| `Monitor` | `Factory/Module/Monitor/Monitor.hpp` | `` | Factory | wrap | P0 | `(interne) aff3ct.factory.Monitor` | done |
| `Puncturer` | `Factory/Module/Puncturer/Puncturer.hpp` | `` | Factory | wrap | P0 | `(interne) aff3ct.factory.Puncturer` | done |
| `Quantizer` | `Factory/Module/Quantizer/Quantizer.hpp` | `` | Factory | wrap | P0 | `(interne) aff3ct.factory.Quantizer` | done |
| `Sink` | `Factory/Module/Sink/Sink.hpp` | `` | Factory | wrap | P0 | `(interne) aff3ct.factory.Sink` | done |
| `Source` | `Factory/Module/Source/Source.hpp` | `` | Factory | wrap | P0 | `(interne) aff3ct.factory.Source` | done |
| `Frozenbits_generator` | `Factory/Tools/Code/Polar/Frozenbits_generator.hpp` | `` | Factory | wrap | P0 | `(interne) aff3ct.factory.Frozenbits_generator` | done |
| `Terminal` | `Factory/Tools/Display/Terminal/Terminal.hpp` | `` | Factory | wrap | P0 | `(interne) aff3ct.factory.Terminal` | done |
| `Interleaver_core` | `Factory/Tools/Interleaver/Interleaver_core.hpp` | `` | Factory | wrap | P0 | `(interne) aff3ct.factory.Interleaver_core` | done |
| `Noise` | `Factory/Tools/Noise/Noise.hpp` | `` | Factory | wrap | P0 | `(interne) aff3ct.factory.Noise` | done |
| `Coset` | `Factory/Module/Coset/Coset.hpp` | `` | Factory | wrap | P1 | `(interne) aff3ct.factory.Coset` | done |
| `Decoder_conv` | `Factory/Module/Decoder/Conv/Decoder_conv.hpp` | `` | Decoder | wrap | P1 | `(interne) aff3ct.factory.Decoder_conv` | done |
| `Decoder_polar_MK` | `Factory/Module/Decoder/Polar_MK/Decoder_polar_MK.hpp` | `` | Decoder | wrap | P1 | `(interne) aff3ct.factory.Decoder_polar_MK` | done |
| `Decoder_polar_PAC` | `Factory/Module/Decoder/Polar_PAC/Decoder_polar_PAC.hpp` | `` | Decoder | wrap | P1 | `(interne) aff3ct.factory.Decoder_polar_PAC` | done |
| `Decoder_polar_PT` | `Factory/Module/Decoder/Polar_PT/Decoder_polar_PT.hpp` | `` | Decoder | wrap | P1 | `(interne) aff3ct.factory.Decoder_polar_PT` | done |
| `Decoder_RA` | `Factory/Module/Decoder/RA/Decoder_RA.hpp` | `` | Decoder | wrap | P1 | `(interne) aff3ct.factory.Decoder_RA` | done |
| `Decoder_RSC` | `Factory/Module/Decoder/RSC/Decoder_RSC.hpp` | `` | Decoder | wrap | P1 | `(interne) aff3ct.factory.Decoder_RSC` | done |
| `Decoder_RSC_DB` | `Factory/Module/Decoder/RSC_DB/Decoder_RSC_DB.hpp` | `` | Decoder | wrap | P1 | `(interne) aff3ct.factory.Decoder_RSC_DB` | done |
| `Decoder_turbo` | `Factory/Module/Decoder/Turbo/Decoder_turbo.hpp` | `class D1 = Decoder_RSC, class D2 = D1` | Decoder | wrap | P1 | `(interne) aff3ct.factory.Decoder_turbo` | done |
| `Decoder_turbo_common` | `Factory/Module/Decoder/Turbo/Decoder_turbo.hpp` | `` |  | wrap | P1 | `(interne) aff3ct.factory.Decoder_turbo_common` | todo |
| `Decoder_turbo_DB` | `Factory/Module/Decoder/Turbo_DB/Decoder_turbo_DB.hpp` | `` | Decoder | wrap | P1 | `(interne) aff3ct.factory.Decoder_turbo_DB` | done |
| `Decoder_turbo_product` | `Factory/Module/Decoder/Turbo_product/Decoder_turbo_product.hpp` | `` | Decoder | wrap | P1 | `(interne) aff3ct.factory.Decoder_turbo_product` | done |
| `Encoder_conv` | `Factory/Module/Encoder/Conv/Encoder_conv.hpp` | `` | Encoder | wrap | P1 | `(interne) aff3ct.factory.Encoder_conv` | done |
| `Encoder_polar_MK` | `Factory/Module/Encoder/Polar_MK/Encoder_polar_MK.hpp` | `` | Encoder | wrap | P1 | `(interne) aff3ct.factory.Encoder_polar_MK` | done |
| `Encoder_polar_PAC` | `Factory/Module/Encoder/Polar_PAC/Encoder_polar_PAC.hpp` | `` | Encoder | wrap | P1 | `(interne) aff3ct.factory.Encoder_polar_PAC` | done |
| `Encoder_polar_PT` | `Factory/Module/Encoder/Polar_PT/Encoder_polar_PT.hpp` | `` | Encoder | wrap | P1 | `(interne) aff3ct.factory.Encoder_polar_PT` | done |
| `Encoder_RA` | `Factory/Module/Encoder/RA/Encoder_RA.hpp` | `` | Encoder | wrap | P1 | `(interne) aff3ct.factory.Encoder_RA` | done |
| `Encoder_RSC` | `Factory/Module/Encoder/RSC/Encoder_RSC.hpp` | `` | Encoder | wrap | P1 | `(interne) aff3ct.factory.Encoder_RSC` | done |
| `Encoder_RSC_DB` | `Factory/Module/Encoder/RSC_DB/Encoder_RSC_DB.hpp` | `` | Encoder | wrap | P1 | `(interne) aff3ct.factory.Encoder_RSC_DB` | done |
| `Encoder_turbo` | `Factory/Module/Encoder/Turbo/Encoder_turbo.hpp` | `class E1 = Encoder_RSC, class E2 = E1` | Encoder | wrap | P1 | `(interne) aff3ct.factory.Encoder_turbo` | done |
| `Encoder_turbo_common` | `Factory/Module/Encoder/Turbo/Encoder_turbo.hpp` | `` |  | wrap | P1 | `(interne) aff3ct.factory.Encoder_turbo_common` | todo |
| `Encoder_turbo_DB` | `Factory/Module/Encoder/Turbo_DB/Encoder_turbo_DB.hpp` | `` | Encoder | wrap | P1 | `(interne) aff3ct.factory.Encoder_turbo_DB` | done |
| `Encoder_turbo_product` | `Factory/Module/Encoder/Turbo_product/Encoder_turbo_product.hpp` | `` | Encoder | wrap | P1 | `(interne) aff3ct.factory.Encoder_turbo_product` | done |
| `Monitor_EXIT` | `Factory/Module/Monitor/EXIT/Monitor_EXIT.hpp` | `` | Monitor | wrap | P1 | `(interne) aff3ct.factory.Monitor_EXIT` | done |
| `Monitor_MI` | `Factory/Module/Monitor/MI/Monitor_MI.hpp` | `` | Monitor | wrap | P1 | `(interne) aff3ct.factory.Monitor_MI` | done |
| `Puncturer_LDPC` | `Factory/Module/Puncturer/LDPC/Puncturer_LDPC.hpp` | `` | Puncturer | wrap | P1 | `(interne) aff3ct.factory.Puncturer_LDPC` | done |
| `Puncturer_polar` | `Factory/Module/Puncturer/Polar/Puncturer_polar.hpp` | `` | Puncturer | wrap | P1 | `(interne) aff3ct.factory.Puncturer_polar` | done |
| `Puncturer_turbo` | `Factory/Module/Puncturer/Turbo/Puncturer_turbo.hpp` | `` | Puncturer | wrap | P1 | `(interne) aff3ct.factory.Puncturer_turbo` | done |
| `Puncturer_turbo_DB` | `Factory/Module/Puncturer/Turbo_DB/Puncturer_turbo_DB.hpp` | `` | Puncturer | wrap | P1 | `(interne) aff3ct.factory.Puncturer_turbo_DB` | done |
| `Frozenbits_generator_MK` | `Factory/Tools/Code/Polar_MK/Frozenbits_generator_MK.hpp` | `` | Factory | wrap | P1 | `(interne) aff3ct.factory.Frozenbits_generator_MK` | done |
| `Polar_code` | `Factory/Tools/Code/Polar_MK/Polar_code.hpp` | `` | Factory | wrap | P1 | `(interne) aff3ct.factory.Polar_code` | done |
| `Pretransform_generator` | `Factory/Tools/Code/Polar_PT/Pretransform_generator.hpp` | `` | Factory | wrap | P1 | `(interne) aff3ct.factory.Pretransform_generator` | done |
| `Flip_and_check` | `Factory/Tools/Code/Turbo/Flip_and_check.hpp` | `` | Factory | wrap | P1 | `(interne) aff3ct.factory.Flip_and_check` | done |
| `Flip_and_check_DB` | `Factory/Tools/Code/Turbo/Flip_and_check_DB.hpp` | `` | Flip_and_check | wrap | P1 | `(interne) aff3ct.factory.Flip_and_check_DB` | done |
| `Scaling_factor` | `Factory/Tools/Code/Turbo/Scaling_factor.hpp` | `` | Factory | wrap | P1 | `(interne) aff3ct.factory.Scaling_factor` | done |
| `Codec_BCH` | `Factory/Tools/Codec/BCH/Codec_BCH.hpp` | `` | Codec_SIHO | wrap | P1 | `(interne) aff3ct.factory.Codec_BCH` | done |
| `Codec` | `Factory/Tools/Codec/Codec.hpp` | `` | Factory | wrap | P1 | `(interne) aff3ct.factory.Codec` | done |
| `Codec_HIHO` | `Factory/Tools/Codec/Codec_HIHO.hpp` | `` | Codec | wrap | P1 | `(interne) aff3ct.factory.Codec_HIHO` | done |
| `Codec_SIHO` | `Factory/Tools/Codec/Codec_SIHO.hpp` | `` | Codec_HIHO | wrap | P1 | `(interne) aff3ct.factory.Codec_SIHO` | done |
| `Codec_SISO` | `Factory/Tools/Codec/Codec_SISO.hpp` | `` | Codec_SIHO | wrap | P1 | `(interne) aff3ct.factory.Codec_SISO` | done |
| `Codec_conv` | `Factory/Tools/Codec/Conv/Codec_conv.hpp` | `` | Codec_SIHO | wrap | P1 | `(interne) aff3ct.factory.Codec_conv` | done |
| `Codec_LDPC` | `Factory/Tools/Codec/LDPC/Codec_LDPC.hpp` | `` | Codec_SISO | wrap | P1 | `(interne) aff3ct.factory.Codec_LDPC` | done |
| `Codec_polar` | `Factory/Tools/Codec/Polar/Codec_polar.hpp` | `` | Codec_SISO | wrap | P1 | `(interne) aff3ct.factory.Codec_polar` | done |
| `Codec_polar_MK` | `Factory/Tools/Codec/Polar_MK/Codec_polar_MK.hpp` | `` | Codec_SIHO | wrap | P1 | `(interne) aff3ct.factory.Codec_polar_MK` | done |
| `Codec_polar_PAC` | `Factory/Tools/Codec/Polar_PAC/Codec_polar_PAC.hpp` | `` | Codec_SISO | wrap | P1 | `(interne) aff3ct.factory.Codec_polar_PAC` | done |
| `Codec_polar_PT` | `Factory/Tools/Codec/Polar_PT/Codec_polar_PT.hpp` | `` | Codec_SISO | wrap | P1 | `(interne) aff3ct.factory.Codec_polar_PT` | done |
| `Codec_RA` | `Factory/Tools/Codec/RA/Codec_RA.hpp` | `` | Codec_SIHO | wrap | P1 | `(interne) aff3ct.factory.Codec_RA` | done |
| `Codec_RS` | `Factory/Tools/Codec/RS/Codec_RS.hpp` | `` | Codec_SIHO | wrap | P1 | `(interne) aff3ct.factory.Codec_RS` | done |
| `Codec_RSC` | `Factory/Tools/Codec/RSC/Codec_RSC.hpp` | `` | Codec_SISO | wrap | P1 | `(interne) aff3ct.factory.Codec_RSC` | done |
| `Codec_RSC_DB` | `Factory/Tools/Codec/RSC_DB/Codec_RSC_DB.hpp` | `` | Codec_SISO | wrap | P1 | `(interne) aff3ct.factory.Codec_RSC_DB` | done |
| `Codec_repetition` | `Factory/Tools/Codec/Repetition/Codec_repetition.hpp` | `` | Codec_SIHO | wrap | P1 | `(interne) aff3ct.factory.Codec_repetition` | done |
| `Codec_turbo` | `Factory/Tools/Codec/Turbo/Codec_turbo.hpp` | `` | Codec_SIHO | wrap | P1 | `(interne) aff3ct.factory.Codec_turbo` | done |
| `Codec_turbo_DB` | `Factory/Tools/Codec/Turbo_DB/Codec_turbo_DB.hpp` | `` | Codec_SIHO | wrap | P1 | `(interne) aff3ct.factory.Codec_turbo_DB` | done |
| `Codec_turbo_product` | `Factory/Tools/Codec/Turbo_product/Codec_turbo_product.hpp` | `` | Codec_SISO | wrap | P1 | `(interne) aff3ct.factory.Codec_turbo_product` | done |
| `Codec_uncoded` | `Factory/Tools/Codec/Uncoded/Codec_uncoded.hpp` | `` | Codec_SISO | wrap | P1 | `(interne) aff3ct.factory.Codec_uncoded` | done |
