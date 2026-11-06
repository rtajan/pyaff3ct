/*!
 * \file
 * \brief Names of the C++ types, as pystreampu dtypes (`streampu.int32.name == "int32"`).
 *
 * pyaff3ct defines no dtype of its own: the Python classes of a template are named after the pystreampu dtypes of
 * their template arguments (`Encoder_int32`, `Decoder_SIHO_int32_float32`) and the Python dispatch
 * (aff3ct/_dispatch.py) builds these names from `streampu.dtype.name`.
 */
#ifndef PYAF_COMMON_TOOLS_DTYPES_HPP_
#define PYAF_COMMON_TOOLS_DTYPES_HPP_

#include <cstdint>
#include <string>

#include "internal/Common/Tools/combos.hpp"

namespace pyaf
{
template<typename T>
struct dtype_name;

#define PYAF_DTYPE_NAME(T, NAME)                                                                                       \
    template<>                                                                                                         \
    struct dtype_name<T>                                                                                               \
    {                                                                                                                  \
        static constexpr const char* value = NAME;                                                                     \
    };

PYAF_DTYPE_NAME(int8_t, "int8")
PYAF_DTYPE_NAME(int16_t, "int16")
PYAF_DTYPE_NAME(int32_t, "int32")
PYAF_DTYPE_NAME(int64_t, "int64")
PYAF_DTYPE_NAME(uint8_t, "uint8")
PYAF_DTYPE_NAME(uint16_t, "uint16")
PYAF_DTYPE_NAME(uint32_t, "uint32")
PYAF_DTYPE_NAME(uint64_t, "uint64")
PYAF_DTYPE_NAME(float, "float32")
PYAF_DTYPE_NAME(double, "float64")
#undef PYAF_DTYPE_NAME

//! "int32_float32" for `types<int32_t, float>`.
template<typename... Ts>
std::string
dtype_suffix(types<Ts...> = {})
{
    std::string s;
    ((s += (s.empty() ? "" : "_") + std::string(dtype_name<Ts>::value)), ...);
    return s;
}

//! Python name of a class template instance: `class_name<int32_t, float>("Decoder_SIHO")` -> "Decoder_SIHO_int32_float32".
template<typename... Ts>
std::string
class_name(const std::string& base)
{
    return base + "_" + dtype_suffix(types<Ts...>{});
}
} // namespace pyaf

#endif // PYAF_COMMON_TOOLS_DTYPES_HPP_
