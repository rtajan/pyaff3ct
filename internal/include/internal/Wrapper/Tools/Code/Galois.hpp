/*!
 * \file
 * \brief Wrappers of the AFF3CT tools: Galois fields and polynomial generators (BCH, RS).
 */
#ifndef PYAF_WRAPPER_TOOLS_CODE_GALOIS_HPP_
#define PYAF_WRAPPER_TOOLS_CODE_GALOIS_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers Galois<I>, BCH_polynomial_generator<I> and RS_polynomial_generator.
void
wrap_galois(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_TOOLS_CODE_GALOIS_HPP_
