/*!
 * \file
 * \brief Wrappers of the debug tools of AFF3CT: Histogram<R>, Frame_trace (text returned instead of written on
 * std::cout) and Dumper (frames recorded when they contain errors).
 */
#ifndef PYAF_WRAPPER_TOOLS_DISPLAY_DEBUG_HPP_
#define PYAF_WRAPPER_TOOLS_DISPLAY_DEBUG_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers Histogram (for each R), Frame_trace and Dumper.
void
wrap_debug_tools(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_TOOLS_DISPLAY_DEBUG_HPP_
