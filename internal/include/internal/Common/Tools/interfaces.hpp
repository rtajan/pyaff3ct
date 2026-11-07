/*!
 * \file
 * \brief Accessors of the AFF3CT interfaces on the module bases (`enc.frozen_bits`, `dec.set_frozen_bits(fb)`...).
 *
 * A module is typed after its most derived wrapped base (`Decoder_SIHO_int32_float32` for a polar SC decoder): its
 * interfaces (tools::Interface_get_set_frozen_bits...) are not Python bases of that class. The accessors of an
 * interface are therefore bound on the bases whose children implement it (from the API fingerprint) and reach the
 * interface with a dynamic_cast; on a module that does not implement it they raise AttributeError, so that
 * `hasattr(dec, "frozen_bits")` tells whether `dec` uses frozen bits.
 */
#ifndef PYAF_COMMON_TOOLS_INTERFACES_HPP_
#define PYAF_COMMON_TOOLS_INTERFACES_HPP_

#include <map>
#include <string>
#include <vector>

#include <pybind11/pybind11.h>

#include "Tools/Interface/Interface_get_set_dynamic_frozen_bits.hpp"
#include "Tools/Interface/Interface_get_set_frozen_bits.hpp"
#include "Tools/Interface/Interface_get_set_pretransform.hpp"
#include "Tools/Interface/Interface_get_trellis.hpp"

namespace pyaf
{
//! Interface I of m, or AttributeError("<class> has no <attr> (it does not implement <interface>)").
template<typename I, typename M>
I&
as_interface(M& m, const char* attr, const char* itf)
{
    if (auto p = dynamic_cast<I*>(&m)) return *p;
    auto obj = pybind11::cast(&m, pybind11::return_value_policy::reference);
    auto cls = pybind11::str(pybind11::type::handle_of(obj).attr("__name__")).cast<std::string>();
    throw pybind11::attribute_error("'" + cls + "' object has no attribute '" + attr + "' (" + itf +
                                    " is not implemented by this module).");
}

//! `frozen_bits` (property) and `set_frozen_bits(fb)`.
template<typename M, typename... O>
void
def_frozen_bits_accessors(pybind11::class_<M, O...>& cls)
{
    using I = aff3ct::tools::Interface_get_set_frozen_bits;
    cls
      .def_property_readonly(
        "frozen_bits",
        [](M& m) { return as_interface<I>(m, "frozen_bits", "Interface_get_set_frozen_bits").get_frozen_bits(); },
        "numpy.ndarray[bool]: frozen bits (True = frozen), polar codes only (AttributeError otherwise).")
      .def(
        "set_frozen_bits",
        [](M& m, const std::vector<bool>& fb)
        { as_interface<I>(m, "set_frozen_bits", "Interface_get_set_frozen_bits").set_frozen_bits(fb); },
        pybind11::arg("frozen_bits"),
        "Set the frozen bits (array-like of N bool), polar codes only.");
}

//! `dynamic_frozen_bits` (property) and `set_dynamic_frozen_bits(fb)`.
template<typename M, typename... O>
void
def_dynamic_frozen_bits_accessors(pybind11::class_<M, O...>& cls)
{
    using I = aff3ct::tools::Interface_get_set_dynamic_frozen_bits;
    const char* itf = "Interface_get_set_dynamic_frozen_bits";
    cls
      .def_property_readonly(
        "dynamic_frozen_bits",
        [itf](M& m) { return as_interface<I>(m, "dynamic_frozen_bits", itf).get_dynamic_frozen_bits(); },
        "numpy.ndarray[bool]: dynamic frozen bits, pre-transformed polar codes only.")
      .def(
        "set_dynamic_frozen_bits",
        [itf](M& m, const std::vector<bool>& fb)
        { as_interface<I>(m, "set_dynamic_frozen_bits", itf).set_dynamic_frozen_bits(fb); },
        pybind11::arg("frozen_bits"),
        "Set the dynamic frozen bits, pre-transformed polar codes only.");
}

//! `pretransform` (property) and `set_pretransform(pt)`.
template<typename M, typename... O>
void
def_pretransform_accessors(pybind11::class_<M, O...>& cls)
{
    using I = aff3ct::tools::Interface_get_set_pretransform;
    const char* itf = "Interface_get_set_pretransform";
    cls
      .def_property_readonly(
        "pretransform",
        [itf](M& m) { return as_interface<I>(m, "pretransform", itf).get_pretransform(); },
        "dict[int, list[int]]: pre-transformation, pre-transformed polar codes only.")
      .def(
        "set_pretransform",
        [itf](M& m, const std::map<uint32_t, std::vector<uint32_t>>& pt)
        { as_interface<I>(m, "set_pretransform", itf).set_pretransform(pt); },
        pybind11::arg("pretransform"),
        "Set the pre-transformation, pre-transformed polar codes only.");
}

//! `trellis` (property).
template<typename M, typename... O>
void
def_trellis_accessor(pybind11::class_<M, O...>& cls)
{
    using I = aff3ct::tools::Interface_get_trellis;
    cls.def_property_readonly(
      "trellis",
      [](M& m) { return as_interface<I>(m, "trellis", "Interface_get_trellis").get_trellis(); },
      "list[list[int]]: trellis, convolutional codes only (RSC, RSC_DB...).");
}
} // namespace pyaf

#endif // PYAF_COMMON_TOOLS_INTERFACES_HPP_
