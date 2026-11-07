/*!
 * \file
 * \brief Noise conversions of aff3ct/Tools/general_utils.h (Eb/N0 <-> Es/N0 <-> sigma).
 */
#ifndef PYAF_WRAPPER_TOOLS_MATH_CONVERSIONS_HPP_
#define PYAF_WRAPPER_TOOLS_MATH_CONVERSIONS_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers sigma_to_esn0, esn0_to_sigma, esn0_to_ebn0 and ebn0_to_esn0 (double precision).
void
wrap_conversions(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_TOOLS_MATH_CONVERSIONS_HPP_
