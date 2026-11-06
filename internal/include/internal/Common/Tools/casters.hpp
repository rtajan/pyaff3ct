/*!
 * \file
 * \brief Automatic conversions between AFF3CT and Python types (Plan.md, rule R7).
 *
 * Must be included (through "internal/internal.hpp") by every translation unit of the extension: a pybind11 caster
 * specialization has to be seen identically everywhere (ODR).
 *
 * - `std::vector<bool>` (frozen bits...) <-> `numpy.ndarray[bool]`; any sequence or array convertible to bool
 *   is accepted as input (numpy array of int, list of bool...).
 */
#ifndef PYAF_COMMON_TOOLS_CASTERS_HPP_
#define PYAF_COMMON_TOOLS_CASTERS_HPP_

#include <vector>

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace pybind11
{
namespace detail
{
template<>
struct type_caster<std::vector<bool>>
{
  public:
    PYBIND11_TYPE_CASTER(std::vector<bool>, io_name("numpy.typing.ArrayLike", "numpy.typing.NDArray[numpy.bool_]"));

    bool load(handle src, bool convert)
    {
        if (!src || src.is_none() || isinstance<str>(src) || isinstance<bytes>(src)) return false;
        if (!convert && !isinstance<array>(src) && !isinstance<sequence>(src)) return false;
        // 1-D array of bool (numpy converts int/float arrays and Python sequences)
        auto arr = array_t<bool, array::c_style | array::forcecast>::ensure(src);
        if (!arr) return false;
        if (arr.ndim() != 1) return false;
        value.assign(arr.data(), arr.data() + arr.size());
        return true;
    }

    static handle cast(const std::vector<bool>& src, return_value_policy /* policy */, handle /* parent */)
    {
        array_t<bool> arr(static_cast<ssize_t>(src.size()));
        auto ptr = arr.mutable_data();
        for (size_t i = 0; i < src.size(); i++)
            ptr[i] = src[i];
        return arr.release();
    }
};
} // namespace detail
} // namespace pybind11

namespace pyaf
{
//! Copy a std::vector into a new numpy array (accessors returning indices, values...).
template<typename T>
pybind11::array_t<T>
to_numpy(const std::vector<T>& v)
{
    pybind11::array_t<T> arr(static_cast<pybind11::ssize_t>(v.size()));
    std::copy(v.begin(), v.end(), arr.mutable_data());
    return arr;
}
} // namespace pyaf

#endif // PYAF_COMMON_TOOLS_CASTERS_HPP_
