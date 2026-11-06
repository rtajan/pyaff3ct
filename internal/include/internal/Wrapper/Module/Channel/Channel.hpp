/*!
 * \file
 * \brief Wrapper of the abstract base aff3ct::module::Channel (see Bases.hpp).
 */
#ifndef PYAF_WRAPPER_MODULE_CHANNEL_CHANNEL_HPP_
#define PYAF_WRAPPER_MODULE_CHANNEL_CHANNEL_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers aff3ct::module::Channel for every dtype combination compiled by AFF3CT.
void
wrap_channel(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_MODULE_CHANNEL_CHANNEL_HPP_
