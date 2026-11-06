#include "Module/CRC/CRC.hpp"

#include "internal/Wrapper/Module/CRC/CRC.hpp"

namespace pyaf
{
namespace wrapper
{
template<typename B>
static void
wrap_crc_internal(py::handle scope)
{
    using C = aff3ct::module::CRC<B>;
    py::class_<C, spu::module::Stateful>(scope,
                                         class_name<B>("CRC").c_str(),
                                         R"pbdoc(Base class of the CRCs.

Tasks: ``build(U_K1 -> U_K2)``, ``extract(V_K1 -> V_K2)``, ``check(V_K)``, ``check_packed(V_K)``.
)pbdoc")
      .def_property_readonly("K", &C::get_K, "int: number of information bits (without the CRC bits).")
      .def_property_readonly(
        "size", [](C& c) { return c.get_size(); }, "int: number of CRC bits.");
}
} // namespace wrapper
} // namespace pyaf

void
pyaf::wrapper::wrap_crc(py::handle scope)
{
    for_each_combo<gen::Module_CRC>([&](auto c) { wrap_crc_internal<typename decltype(c)::template at<0>>(scope); });
}
