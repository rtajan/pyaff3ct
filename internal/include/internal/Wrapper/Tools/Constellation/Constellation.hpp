/*!
 * \file
 * \brief Wrappers of aff3ct::tools::Constellation<R> and of its children (PAM, PSK, QAM, user).
 */
#ifndef PYAF_WRAPPER_TOOLS_CONSTELLATION_CONSTELLATION_HPP_
#define PYAF_WRAPPER_TOOLS_CONSTELLATION_CONSTELLATION_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers Constellation and its children for each R.
void
wrap_constellations(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_TOOLS_CONSTELLATION_CONSTELLATION_HPP_
