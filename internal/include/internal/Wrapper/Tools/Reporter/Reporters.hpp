/*!
 * \file
 * \brief Wrappers of the AFF3CT tools: Reporters for streampu.Terminal_std (BFER, noise, throughput).
 */
#ifndef PYAF_WRAPPER_TOOLS_REPORTER_REPORTERS_HPP_
#define PYAF_WRAPPER_TOOLS_REPORTER_REPORTERS_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers Reporter_BFER<B>, Reporter_noise<R> and Reporter_throughput (after the modules).
void
wrap_reporters(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_TOOLS_REPORTER_REPORTERS_HPP_
