/*!
 * \file
 * \brief Wrapper of the abstract base aff3ct::module::Decoder (see Bases.hpp).
 */
#ifndef PYAF_WRAPPER_MODULE_DECODER_DECODER_HPP_
#define PYAF_WRAPPER_MODULE_DECODER_DECODER_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers aff3ct::module::Decoder for every dtype combination compiled by AFF3CT.
void
wrap_decoder(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_MODULE_DECODER_DECODER_HPP_
