#include "Module/Quantizer/Quantizer.hpp"

#include "internal/Wrapper/Module/Quantizer/Quantizer.hpp"

namespace pyaf
{
namespace wrapper
{
template<typename R, typename Q>
static void
wrap_quantizer_internal(py::handle scope)
{
    using Qz = aff3ct::module::Quantizer<R, Q>;
    py::class_<Qz, spu::module::Stateful>(scope,
                                          class_name<R, Q>("Quantizer").c_str(),
                                          R"pbdoc(Base class of the quantizers.

Task: ``process(Y_N1 -> Y_N2)``.
)pbdoc")
      .def_property_readonly("N", &Qz::get_N, "int: frame size.");
}
} // namespace wrapper
} // namespace pyaf

void
pyaf::wrapper::wrap_quantizer(py::handle scope)
{
    for_each_combo<gen::Module_Quantizer>(
      [&](auto c)
      {
          using T = decltype(c);
          wrap_quantizer_internal<typename T::template at<0>, typename T::template at<1>>(scope);
      });
}
