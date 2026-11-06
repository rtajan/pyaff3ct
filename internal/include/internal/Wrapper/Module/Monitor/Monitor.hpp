/*!
 * \file
 * \brief Wrapper of the abstract base aff3ct::module::Monitor (see Bases.hpp).
 */
#ifndef PYAF_WRAPPER_MODULE_MONITOR_MONITOR_HPP_
#define PYAF_WRAPPER_MODULE_MONITOR_MONITOR_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers aff3ct::module::Monitor for every dtype combination compiled by AFF3CT.
void
wrap_monitor(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_MODULE_MONITOR_MONITOR_HPP_
