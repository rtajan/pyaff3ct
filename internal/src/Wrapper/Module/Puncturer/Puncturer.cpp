#include "Module/Puncturer/Puncturer.hpp"

#include "internal/Wrapper/Module/Puncturer/Puncturer.hpp"

namespace pyaf
{
namespace wrapper
{
template<typename B, typename Q>
static void
wrap_puncturer_internal(py::handle scope)
{
    using P = aff3ct::module::Puncturer<B, Q>;
    py::class_<P, spu::module::Stateful>(scope,
                                         class_name<B, Q>("Puncturer").c_str(),
                                         R"pbdoc(Base class of the puncturers.

Tasks: ``puncture(X_N1 -> X_N2)``, ``depuncture(Y_N1 -> Y_N2)``.
)pbdoc")
      .def_property_readonly("K", &P::get_K, "int: number of information bits.")
      .def_property_readonly("N", &P::get_N, "int: frame size after puncturing.")
      .def_property_readonly("N_cw", &P::get_N_cw, "int: codeword size before puncturing.");
}
} // namespace wrapper
} // namespace pyaf

void
pyaf::wrapper::wrap_puncturer(py::handle scope)
{
    for_each_combo<gen::Module_Puncturer>(
      [&](auto c)
      {
          using T = decltype(c);
          wrap_puncturer_internal<typename T::template at<0>, typename T::template at<1>>(scope);
      });
}
