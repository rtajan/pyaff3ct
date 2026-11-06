/*!
 * \file
 * \brief Wrappers of the AFF3CT interfaces (aff3ct::tools::Interface_*).
 *
 * Interfaces are bound without constructor: they exist so that the modules inheriting them expose their methods
 * (and `isinstance(obj, aff3ct.interfaces.Interface_get_set_frozen_bits)` works). The StreamPU interfaces
 * (`spu::tools::Interface_set_seed`, `_reset`, `_is_done`, `_clone`, `_get_set_n_frames`) come from pystreampu.
 */
#ifndef PYAF_WRAPPER_TOOLS_INTERFACE_INTERFACES_HPP_
#define PYAF_WRAPPER_TOOLS_INTERFACE_INTERFACES_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
void
wrap_interface_get_set_frozen_bits(py::handle scope);
void
wrap_interface_get_set_dynamic_frozen_bits(py::handle scope);
void
wrap_interface_get_set_pretransform(py::handle scope);
void
wrap_interface_get_trellis(py::handle scope);
void
wrap_interface_get_set_noise(py::handle scope);
void
wrap_interface_notify_noise_update(py::handle scope);

//! Registers the six interfaces (Interface_get_set_noise needs tools::Noise, see wrap_noise).
void
wrap_interfaces(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_TOOLS_INTERFACE_INTERFACES_HPP_
