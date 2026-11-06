/*!
 * \file
 * \brief Wrapper of the abstract base aff3ct::module::Encoder (see Bases.hpp).
 */
#ifndef PYAF_WRAPPER_MODULE_ENCODER_ENCODER_HPP_
#define PYAF_WRAPPER_MODULE_ENCODER_ENCODER_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers aff3ct::module::Encoder for every dtype combination compiled by AFF3CT.
void
wrap_encoder(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_MODULE_ENCODER_ENCODER_HPP_
