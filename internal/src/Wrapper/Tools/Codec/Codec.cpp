#include "Tools/Codec/Codec.hpp"
#include "Tools/Codec/BCH/Codec_BCH.hpp"
#include "Tools/Codec/Codec_HIHO.hpp"
#include "Tools/Codec/Codec_SIHO.hpp"
#include "Tools/Codec/Codec_SISO.hpp"
#include "Tools/Codec/Conv/Codec_conv.hpp"
#include "Tools/Codec/LDPC/Codec_LDPC.hpp"
#include "Tools/Codec/Polar/Codec_polar.hpp"
#include "Tools/Codec/Polar_MK/Codec_polar_MK.hpp"
#include "Tools/Codec/Polar_PAC/Codec_polar_PAC.hpp"
#include "Tools/Codec/Polar_PT/Codec_polar_PT.hpp"
#include "Tools/Codec/RA/Codec_RA.hpp"
#include "Tools/Codec/RS/Codec_RS.hpp"
#include "Tools/Codec/RSC/Codec_RSC.hpp"
#include "Tools/Codec/RSC_DB/Codec_RSC_DB.hpp"
#include "Tools/Codec/Repetition/Codec_repetition.hpp"
#include "Tools/Codec/Turbo/Codec_turbo.hpp"
#include "Tools/Codec/Turbo_DB/Codec_turbo_DB.hpp"
#include "Tools/Codec/Turbo_product/Codec_turbo_product.hpp"
#include "Tools/Codec/Uncoded/Codec_uncoded.hpp"

#include "internal/Wrapper/Tools/Codec/Codec.hpp"

using namespace aff3ct::tools;

namespace pyaf
{
namespace wrapper
{
//! Getter returning None when AFF3CT throws because the object is not part of the codec ("'puncturer' is NULL.").
template<typename C, typename G>
static auto
optional(G getter)
{
    return [getter](C& c) -> py::object
    {
        try
        {
            auto& obj = (c.*getter)();
            return py::cast(&obj, py::return_value_policy::reference_internal, py::cast(&c));
        }
        catch (const spu::tools::runtime_error&)
        {
            return py::none();
        }
    };
}

template<typename B, typename Q>
static void
wrap_codec_bases(py::handle scope)
{
    using C = Codec<B, Q>;
    py::class_<C, Interface_get_set_noise, Interface_notify_noise_update, spu::tools::Interface_get_set_n_frames>(
      scope,
      class_name<B, Q>("Codec").c_str(),
      R"pbdoc(Base class of the codecs: builds and connects the modules of a code family.

The modules are owned by the codec (properties, ``None`` when the codec has no such module); they keep the codec
alive. ``set_noise(noise)`` gives the noise to the modules that need it (adaptive frozen bits of the polar codes,
scaling factors of the turbo codes...).
)pbdoc")
      .def_property_readonly(
        "encoder", &C::get_encoder, py::return_value_policy::reference_internal, "aff3ct.enc.Encoder: encoder.")
      .def_property_readonly("puncturer", optional<C>(&C::get_puncturer), "aff3ct.pct.Puncturer or None: puncturer.")
      .def_property_readonly(
        "extractor", optional<C>(&C::get_extractor), "aff3ct.ext.Extractor or None: extractor (turbo schemes).")
      .def_property_readonly(
        "interleaver", optional<C>(&C::get_interleaver), "aff3ct.tools.Interleaver_core or None: interleaver core.");

    using H = Codec_HIHO<B, Q>;
    py::class_<H, C>(scope, class_name<B, Q>("Codec_HIHO").c_str(), "Codec with a hard-input hard-output decoder.")
      .def_property_readonly("decoder_hiho",
                             optional<H>(&H::get_decoder_hiho),
                             "aff3ct.dec.Decoder_HIHO or None: hard-input hard-output decoder.");
    using S = Codec_SIHO<B, Q>;
    py::class_<S, H>(scope, class_name<B, Q>("Codec_SIHO").c_str(), "Codec with a soft-input hard-output decoder.")
      .def_property_readonly("decoder_siho",
                             optional<S>(&S::get_decoder_siho),
                             "aff3ct.dec.Decoder_SIHO or None: soft-input hard-output decoder.");
    using O = Codec_SISO<B, Q>;
    py::class_<O, S>(scope, class_name<B, Q>("Codec_SISO").c_str(), "Codec with a soft-input soft-output decoder.")
      .def_property_readonly(
        "decoder_siso",
        optional<O>(&O::get_decoder_siso),
        "aff3ct.dec.Decoder_SISO or None: soft-input soft-output decoder (None if the decoder type has none).");
}

template<typename B, typename Q>
static void
wrap_codecs_internal(py::handle scope)
{
    using O = Codec_SISO<B, Q>;
    using S = Codec_SIHO<B, Q>;
#define PYAF_CODEC(CLASS, BASE, DOC) py::class_<CLASS<B, Q>, BASE>(scope, class_name<B, Q>(#CLASS).c_str(), DOC)

    PYAF_CODEC(Codec_BCH, S, "Codec of the BCH codes.")
      .def_property_readonly("GF",
                             &Codec_BCH<B, Q>::get_GF_poly,
                             py::return_value_policy::reference_internal,
                             "aff3ct.tools.BCH_polynomial_generator: generator polynomial.");
    PYAF_CODEC(Codec_RS, S, "Codec of the Reed-Solomon codes.")
      .def_property_readonly("GF",
                             &Codec_RS<B, Q>::get_GF_poly,
                             py::return_value_policy::reference_internal,
                             "aff3ct.tools.RS_polynomial_generator: generator polynomial.");
    PYAF_CODEC(Codec_LDPC, O, "Codec of the LDPC codes.")
      .def_property_readonly(
        "H", &Codec_LDPC<B, Q>::get_H, py::return_value_policy::reference_internal, "aff3ct.tools.Sparse_matrix: H.")
      .def_property_readonly(
        "G", &Codec_LDPC<B, Q>::get_G, py::return_value_policy::reference_internal, "aff3ct.tools.Sparse_matrix: G.")
      .def_property_readonly(
        "info_bits_pos",
        [](const Codec_LDPC<B, Q>& c) { return to_numpy(c.get_info_bits_pos()); },
        "numpy.ndarray[uint32]: positions of the information bits.");
    PYAF_CODEC(Codec_RSC, O, "Codec of the recursive systematic convolutional codes.")
      .def("is_buffered_encoding", &Codec_RSC<B, Q>::is_buffered_encoding)
      .def_property_readonly("trellis", &Codec_RSC<B, Q>::get_trellis, "list[list[int]]: trellis.");
    PYAF_CODEC(Codec_RSC_DB, O, "Codec of the double-binary RSC codes.")
      .def("is_buffered_encoding", &Codec_RSC_DB<B, Q>::is_buffered_encoding)
      .def_property_readonly("trellis", &Codec_RSC_DB<B, Q>::get_trellis, "list[list[int]]: trellis.");
    PYAF_CODEC(Codec_conv, S, "Codec of the convolutional codes (Viterbi).")
      .def_property_readonly("trellis", &Codec_conv<B, Q>::get_trellis, "list[list[int]]: trellis.");
    PYAF_CODEC(Codec_turbo, S, "Codec of the turbo codes.")
      .def_property_readonly("trellis", &Codec_turbo<B, Q>::get_trellis, "list[list[int]]: trellis.");
    PYAF_CODEC(Codec_turbo_DB, S, "Codec of the double-binary turbo codes.")
      .def_property_readonly("trellis", &Codec_turbo_DB<B, Q>::get_trellis, "list[list[int]]: trellis.");
    PYAF_CODEC(Codec_turbo_product, O, "Codec of the turbo product codes.")
      .def_property_readonly("GF",
                             &Codec_turbo_product<B, Q>::get_GF_poly,
                             py::return_value_policy::reference_internal,
                             "aff3ct.tools.BCH_polynomial_generator: generator polynomial of the BCH sub-codes.");
    PYAF_CODEC(Codec_RA, S, "Codec of the repeat-accumulate codes.");
    PYAF_CODEC(Codec_repetition, S, "Codec of the repetition codes.");
    PYAF_CODEC(Codec_uncoded, O, "Codec without coding.");

    using P = Codec_polar<B, Q>;
    py::class_<P, O, Interface_get_set_frozen_bits>(
      scope, class_name<B, Q>("Codec_polar").c_str(), "Codec of the polar codes (frozen bits adapted to the noise).")
      .def("is_adaptive_frozen_bits", &P::is_adaptive_frozen_bits, "True if set_noise() regenerates the frozen bits.")
      .def("is_generated_decoder", &P::is_generated_decoder)
      .def_property_readonly("frozen_bits_generator",
                             &P::get_frozen_bits_generator,
                             py::return_value_policy::reference_internal,
                             "aff3ct.tools.Frozenbits_generator: frozen bits generator.");
    using MK = Codec_polar_MK<B, Q>;
    py::class_<MK, S, Interface_get_set_frozen_bits>(
      scope, class_name<B, Q>("Codec_polar_MK").c_str(), "Codec of the multi-kernel polar codes.")
      .def("is_adaptive_frozen_bits", &MK::is_adaptive_frozen_bits)
      .def_property_readonly("frozen_bits_generator",
                             &MK::get_frozen_bits_generator,
                             py::return_value_policy::reference_internal,
                             "aff3ct.tools.Frozenbits_generator: frozen bits generator.");
    using PAC = Codec_polar_PAC<B, Q>;
    py::class_<PAC, O, Interface_get_set_frozen_bits>(
      scope, class_name<B, Q>("Codec_polar_PAC").c_str(), "Codec of the polarization-adjusted convolutional codes.")
      .def("is_adaptive_frozen_bits", &PAC::is_adaptive_frozen_bits)
      .def_property_readonly("frozen_bits_generator",
                             &PAC::get_frozen_bits_generator,
                             py::return_value_policy::reference_internal,
                             "aff3ct.tools.Frozenbits_generator: frozen bits generator.");
    using PT = Codec_polar_PT<B, Q>;
    py::class_<PT,
               O,
               Interface_get_set_frozen_bits,
               Interface_get_set_pretransform,
               Interface_get_set_dynamic_frozen_bits>(
      scope, class_name<B, Q>("Codec_polar_PT").c_str(), "Codec of the pre-transformed polar codes.")
      .def_property_readonly("frozen_bits_generator",
                             &PT::get_frozen_bits_generator,
                             py::return_value_policy::reference_internal,
                             "aff3ct.tools.Frozenbits_generator: frozen bits generator.");
#undef PYAF_CODEC
}
} // namespace wrapper
} // namespace pyaf

void
pyaf::wrapper::wrap_codecs(py::handle scope)
{
    for_each_combo<gen::Tools_Codec>(
      [&](auto c)
      {
          using T = decltype(c);
          wrap_codec_bases<typename T::template at<0>, typename T::template at<1>>(scope);
          wrap_codecs_internal<typename T::template at<0>, typename T::template at<1>>(scope);
      });
}
