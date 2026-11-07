/*!
 * \file
 * \brief Wrappers of aff3ct::tools::Interleaver_core<T> and of its children (NO, random, LTE, CCSDS, user...).
 *
 * Python names: `Interleaver_core_uint32`, `Interleaver_core_random_uint32`... (one class per T compiled by AFF3CT);
 * `aff3ct.tools.Interleaver_core_random(size)` builds the default instance (T = uint32, the one used by the
 * interleaver modules).
 */
#ifndef PYAF_WRAPPER_TOOLS_INTERLEAVER_INTERLEAVER_CORE_HPP_
#define PYAF_WRAPPER_TOOLS_INTERLEAVER_INTERLEAVER_CORE_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers Interleaver_core and its children for each T.
void
wrap_interleaver_core(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_TOOLS_INTERLEAVER_INTERLEAVER_CORE_HPP_
