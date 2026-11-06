#include "Module/Encoder/Encoder.hpp"

#include "internal/Wrapper/Module/Encoder/Encoder.hpp"

namespace pyaf
{
namespace wrapper
{
template<typename B>
static void
wrap_encoder_internal(py::handle scope)
{
    using E = aff3ct::module::Encoder<B>;
    py::class_<E, spu::module::Stateful, spu::tools::Interface_set_seed>(scope,
                                                                         class_name<B>("Encoder").c_str(),
                                                                         R"pbdoc(Base class of the encoders.

Task: ``encode(U_K -> X_N)``.
)pbdoc")
      .def_property_readonly("K", &E::get_K, "int: number of information bits.")
      .def_property_readonly("N", &E::get_N, "int: codeword size.")
      .def("is_sys", &E::is_sys, "Return True if the code is systematic.")
      .def_property_readonly("tail_length", &E::tail_length, "int: number of tail bits.")
      .def("is_memorizing", &E::is_memorizing, "Return True if the encoder keeps its last encoded frames.")
      .def("set_memorizing",
           &E::set_memorizing,
           "memorizing"_a,
           "Keep (or not) the last encoded frames (needed by some genie-aided decoders).")
      .def_property_readonly(
        "info_bits_pos",
        [](const E& e) { return to_numpy(e.get_info_bits_pos()); },
        "numpy.ndarray[uint32]: positions of the information bits in the codeword.")
      .def(
        "is_codeword",
        [](E& e, py::array_t<B, py::array::c_style | py::array::forcecast> X_N)
        {
            if (X_N.size() != e.get_N())
                throw py::value_error("'X_N' must contain N=" + std::to_string(e.get_N()) + " elements (got " +
                                      std::to_string(X_N.size()) + ").");
            return e.is_codeword(X_N.data());
        },
        "X_N"_a,
        "Return True if X_N (N bits) is a codeword.");
    add_module_class<E>();
}
} // namespace wrapper
} // namespace pyaf

void
pyaf::wrapper::wrap_encoder(py::handle scope)
{
    for_each_combo<gen::Module_Encoder>([&](auto c)
                                        { wrap_encoder_internal<typename decltype(c)::template at<0>>(scope); });
}
