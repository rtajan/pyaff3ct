/*!
 * \file
 * \brief Wrapper of aff3ct::factory::Factory and helpers to bind the factories (Plan.md, rule R5).
 *
 * Factories are an implementation detail of the module-level functions (`aff3ct.crc.polynomial(...)` creates a
 * factory, sets its parameters and calls a builder). They remain reachable in `aff3ct.factory` for the advanced
 * uses: `from_cli()` (exact parity with the AFF3CT command line), `headers()`, `print_help()`, `clone()`.
 *
 * Each concrete factory binds its public parameters with `def_param` (which also records their names in the
 * `_parameters` class attribute, used by the Python layer to reject unknown keywords) and its builders with
 * `def_builders` (one method per dtype combination compiled by AFF3CT: `build_int32`, `build_int32_float32`...).
 */
#ifndef PYAF_WRAPPER_FACTORY_FACTORY_HPP_
#define PYAF_WRAPPER_FACTORY_FACTORY_HPP_

#include "Factory/Factory.hpp"

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers aff3ct::factory::Factory (abstract) in `scope`.
void
wrap_factory(py::handle scope);

/*!
 * \brief Binds a public parameter of a factory as a read/write attribute and records its name.
 *
 * \code
 * def_param(cls, "implem", &aff3ct::factory::CRC::implem, "Implementation: 'STD', 'FAST' or 'INTER'.");
 * \endcode
 */
template<typename Cls, typename F, typename T>
Cls&
def_param(Cls& cls, const char* name, T F::*member, const char* doc)
{
    cls.def_readwrite(name, member, doc);
    py::tuple params = py::getattr(cls, "_parameters", py::tuple());
    py::list l(params);
    l.append(name);
    cls.attr("_parameters") = py::tuple(l);
    return cls;
}

/*!
 * \brief Binds one builder method per dtype combination: `<name>_<dtypes>` (e.g. `build_int32`).
 *
 * `Combos` is a `pyaf::gen::Factory_<Name>__<builder>` alias. `make` receives a `types<...>` tag and returns the
 * (non-generic) callable to bind for this combination; the built object is owned by Python.
 *
 * \code
 * def_builders<gen::Factory_CRC__build>(cls, "build", [](auto c) {
 *     using B = typename decltype(c)::template at<0>;
 *     return [](const aff3ct::factory::CRC& f) { return f.build<B>(); };
 * });
 * \endcode
 */
template<typename Combos, typename Cls, typename Make, typename... Extra>
Cls&
def_builders(Cls& cls, const std::string& name, Make&& make, const Extra&... extra)
{
    for_each_combo<Combos>(
      [&](auto c)
      {
          cls.def((name + "_" + dtype_suffix(decltype(c){})).c_str(),
                  make(c),
                  py::return_value_policy::take_ownership,
                  extra...);
      });
    return cls;
}
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_FACTORY_FACTORY_HPP_
