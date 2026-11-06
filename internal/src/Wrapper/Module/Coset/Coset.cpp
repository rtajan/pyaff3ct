#include "Module/Coset/Coset.hpp"

#include "internal/Wrapper/Module/Coset/Coset.hpp"

namespace pyaf
{
namespace wrapper
{
template<typename B, typename D>
static void
wrap_coset_internal(py::handle scope)
{
    using C = aff3ct::module::Coset<B, D>;
    py::class_<C, spu::module::Stateful>(scope,
                                         class_name<B, D>("Coset").c_str(),
                                         R"pbdoc(Base class of the cosets (all-zero codeword simulations).

Task: ``apply(ref, in -> out)``.
)pbdoc")
      .def_property_readonly("size", &C::get_size, "int: frame size.");
}
} // namespace wrapper
} // namespace pyaf

void
pyaf::wrapper::wrap_coset(py::handle scope)
{
    for_each_combo<gen::Module_Coset>(
      [&](auto c)
      {
          using T = decltype(c);
          wrap_coset_internal<typename T::template at<0>, typename T::template at<1>>(scope);
      });
}
