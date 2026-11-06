/*!
 * \file
 * \brief Wrappers of aff3ct::tools::Noise<R> and of its children (Sigma, Event_probability, Received_optical_power).
 *
 * Python names: `Noise_float32`, `Sigma_float32`... (one class per R compiled by AFF3CT, see Generated/instantiations).
 */
#ifndef PYAF_WRAPPER_TOOLS_NOISE_NOISE_HPP_
#define PYAF_WRAPPER_TOOLS_NOISE_NOISE_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
template<typename R>
void
wrap_noise_internal(py::handle scope);

//! Registers the Noise_type enum and Noise / Sigma / Event_probability / Received_optical_power for each R.
void
wrap_noise(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#ifndef DOXYGEN_SHOULD_SKIP_THIS
#include "internal/Wrapper/Tools/Noise/Noise.hxx"
#endif

#endif // PYAF_WRAPPER_TOOLS_NOISE_NOISE_HPP_
