#include "Module/Extractor/Extractor.hpp"

#include "internal/Wrapper/Module/Extractor/Extractor.hpp"

namespace pyaf
{
namespace wrapper
{
template<typename B, typename Q>
static void
wrap_extractor_internal(py::handle scope)
{
    using X = aff3ct::module::Extractor<B, Q>;
    py::class_<X, spu::module::Stateful>(scope,
                                         class_name<B, Q>("Extractor").c_str(),
                                         R"pbdoc(Base class of the extractors (systematic/parity LLRs, used by turbo schemes).

Tasks: ``get_sys_llr``, ``get_sys_bit``, ``get_sys_and_par_llr``, ``add_sys_and_ext_llr``.
)pbdoc");
}
} // namespace wrapper
} // namespace pyaf

void
pyaf::wrapper::wrap_extractor(py::handle scope)
{
    for_each_combo<gen::Module_Extractor>(
      [&](auto c)
      {
          using T = decltype(c);
          wrap_extractor_internal<typename T::template at<0>, typename T::template at<1>>(scope);
      });
}
