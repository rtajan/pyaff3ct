#include "Module/Decoder/Decoder.hpp"
#include "Module/Decoder/Decoder_HIHO.hpp"
#include "Module/Decoder/Decoder_SIHO.hpp"
#include "Module/Decoder/Decoder_SISO.hpp"

#include "internal/Wrapper/Module/Decoder/Decoder.hpp"

namespace pyaf
{
namespace wrapper
{
template<typename B>
static void
wrap_decoder_hiho_internal(py::handle scope)
{
    using D = aff3ct::module::Decoder_HIHO<B>;
    py::class_<D, aff3ct::module::Decoder>(scope,
                                           class_name<B>("Decoder_HIHO").c_str(),
                                           R"pbdoc(Hard-input hard-output decoder.

Tasks: ``decode_hiho(Y_N -> V_K)``, ``decode_hiho_cw(Y_N -> V_N)`` (``CWD``: socket of the corrected-codeword flag).
)pbdoc");
    add_module_class<D>();
}

template<typename B, typename R>
static void
wrap_decoder_siho_internal(py::handle scope)
{
    using D = aff3ct::module::Decoder_SIHO<B, R>;
    py::class_<D, aff3ct::module::Decoder_HIHO<B>>(scope,
                                                   class_name<B, R>("Decoder_SIHO").c_str(),
                                                   R"pbdoc(Soft-input hard-output decoder (also HIHO).

Tasks: ``decode_siho(Y_N -> V_K)``, ``decode_siho_cw(Y_N -> V_N)``.
)pbdoc");
    add_module_class<D>();
}

template<typename B, typename R>
static void
wrap_decoder_siso_internal(py::handle scope)
{
    using D = aff3ct::module::Decoder_SISO<B, R>;
    py::class_<D, aff3ct::module::Decoder_SIHO<B, R>>(scope,
                                                      class_name<B, R>("Decoder_SISO").c_str(),
                                                      R"pbdoc(Soft-input soft-output decoder (also SIHO and HIHO).

Tasks: ``decode_siso(Y_N1 -> Y_N2)``, ``decode_siso_alt(sys, par -> ext)``.
)pbdoc")
      .def_property_readonly("tail_length", &D::tail_length, "int: number of tail bits.");
    add_module_class<D>();
}
} // namespace wrapper
} // namespace pyaf

void
pyaf::wrapper::wrap_decoder(py::handle scope)
{
    using aff3ct::module::Decoder;
    py::class_<Decoder, spu::module::Stateful, spu::tools::Interface_set_seed, spu::tools::Interface_reset>(
      scope, "Decoder", "Base class of the decoders.")
      .def_property_readonly("K", &Decoder::get_K, "int: number of information bits.")
      .def_property_readonly("N", &Decoder::get_N, "int: codeword size.")
      .def("is_auto_reset", &Decoder::is_auto_reset, "Return True if the decoder state is reset before each frame.")
      .def("set_auto_reset",
           &Decoder::set_auto_reset,
           "auto_reset"_a,
           "Reset (or not) the decoder state before each frame (default True).");
    add_module_class<Decoder>();

    for_each_combo<gen::Module_Decoder_HIHO>(
      [&](auto c) { wrap_decoder_hiho_internal<typename decltype(c)::template at<0>>(scope); });
    for_each_combo<gen::Module_Decoder_SIHO>(
      [&](auto c)
      {
          using T = decltype(c);
          wrap_decoder_siho_internal<typename T::template at<0>, typename T::template at<1>>(scope);
      });
    for_each_combo<gen::Module_Decoder_SISO>(
      [&](auto c)
      {
          using T = decltype(c);
          wrap_decoder_siso_internal<typename T::template at<0>, typename T::template at<1>>(scope);
      });
}
