/*!
 * \file
 * \brief Wrapper of the abstract base aff3ct::module::Puncturer (see Bases.hpp).
 */
#ifndef PYAF_WRAPPER_MODULE_PUNCTURER_PUNCTURER_HPP_
#define PYAF_WRAPPER_MODULE_PUNCTURER_PUNCTURER_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers aff3ct::module::Puncturer for every dtype combination compiled by AFF3CT.
void
wrap_puncturer(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_MODULE_PUNCTURER_PUNCTURER_HPP_
