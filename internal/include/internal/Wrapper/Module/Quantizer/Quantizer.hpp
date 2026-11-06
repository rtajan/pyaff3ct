/*!
 * \file
 * \brief Wrapper of the abstract base aff3ct::module::Quantizer (see Bases.hpp).
 */
#ifndef PYAF_WRAPPER_MODULE_QUANTIZER_QUANTIZER_HPP_
#define PYAF_WRAPPER_MODULE_QUANTIZER_QUANTIZER_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers aff3ct::module::Quantizer for every dtype combination compiled by AFF3CT.
void
wrap_quantizer(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_MODULE_QUANTIZER_QUANTIZER_HPP_
