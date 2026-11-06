#include "Module/Modem/Modem.hpp"

#include "internal/Wrapper/Module/Modem/Modem.hpp"

namespace pyaf
{
namespace wrapper
{
template<typename B, typename R, typename Q>
static void
wrap_modem_internal(py::handle scope)
{
    using M = aff3ct::module::Modem<B, R, Q>;
    py::class_<M, spu::module::Stateful>(scope,
                                         class_name<B, R, Q>("Modem").c_str(),
                                         R"pbdoc(Base class of the modems.

Tasks: ``modulate(X_N1 -> X_N2)``, ``filter(CP, Y_N1 -> Y_N2)``, ``demodulate(CP, Y_N1 -> Y_N2)``,
``demodulate_wg(CP, H_N, Y_N1 -> Y_N2)``, ``tmodulate``, ``tdemodulate``, ``tdemodulate_wg``.
)pbdoc")
      .def_property_readonly("N", &M::get_N, "int: number of bits per frame.")
      .def_property_readonly("N_mod", &M::get_N_mod, "int: number of real values after modulation.")
      .def_property_readonly("N_fil", &M::get_N_fil, "int: number of real values after filtering.")
      .def("is_demodulator", &M::is_demodulator, "Return True if the modem can demodulate.")
      .def("is_filter", &M::is_filter, "Return True if the modem has a filter (task ``filter``).");
}
} // namespace wrapper
} // namespace pyaf

void
pyaf::wrapper::wrap_modem(py::handle scope)
{
    for_each_combo<gen::Module_Modem>(
      [&](auto c)
      {
          using T = decltype(c);
          wrap_modem_internal<typename T::template at<0>, typename T::template at<1>, typename T::template at<2>>(
            scope);
      });
}
