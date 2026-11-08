/*!
 * \file
 * \brief Wrappers of aff3ct::tools::Distribution<R> and Distributions<R> (noise distributions read from a file:
 * optical channel and OOK optical modem).
 */
#ifndef PYAF_WRAPPER_TOOLS_MATH_DISTRIBUTIONS_HPP_
#define PYAF_WRAPPER_TOOLS_MATH_DISTRIBUTIONS_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers Distribution_mode, Distribution and Distributions for each R.
void
wrap_distributions(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_TOOLS_MATH_DISTRIBUTIONS_HPP_
