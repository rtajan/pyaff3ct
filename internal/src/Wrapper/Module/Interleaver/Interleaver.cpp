#include "Module/Interleaver/Interleaver.hpp"

#include "internal/Wrapper/Module/Interleaver/Interleaver.hpp"

namespace pyaf
{
namespace wrapper
{
template<typename D, typename T>
static void
wrap_interleaver_internal(py::handle scope)
{
    using I = aff3ct::module::Interleaver<D, T>;
    using C = aff3ct::tools::Interleaver_core<T>;
    py::class_<I, spu::module::Stateful>(scope,
                                         class_name<D, T>("Interleaver").c_str(),
                                         R"pbdoc(Interleaver: applies the permutation of an interleaver core.

Tasks: ``interleave(nat -> itl)``, ``deinterleave(itl -> nat)`` and their ``*_reordering`` variants (one
permutation per frame, uniform cores). The core is shared, not copied: a uniform core drawn again
(``core.refresh()``) changes the permutation of every interleaver that uses it.

Args:
    core (aff3ct.tools.Interleaver_core): permutation (kept alive by the interleaver).
)pbdoc")
      .def(py::init<const C&>(), "core"_a, py::keep_alive<1, 2>())
      .def_property_readonly("core",
                             &I::get_core,
                             py::return_value_policy::reference_internal,
                             "aff3ct.tools.Interleaver_core: permutation.");
    add_module_class<I>();
}
} // namespace wrapper
} // namespace pyaf

void
pyaf::wrapper::wrap_interleaver(py::handle scope)
{
    for_each_combo<gen::Module_Interleaver>(
      [&](auto c)
      {
          using C = decltype(c);
          wrap_interleaver_internal<typename C::template at<0>, typename C::template at<1>>(scope);
      });
}
