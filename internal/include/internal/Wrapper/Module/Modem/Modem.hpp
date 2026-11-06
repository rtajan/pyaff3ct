/*!
 * \file
 * \brief Wrapper of the abstract base aff3ct::module::Modem (see Bases.hpp).
 */
#ifndef PYAF_WRAPPER_MODULE_MODEM_MODEM_HPP_
#define PYAF_WRAPPER_MODULE_MODEM_MODEM_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers aff3ct::module::Modem for every dtype combination compiled by AFF3CT.
void
wrap_modem(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_MODULE_MODEM_MODEM_HPP_
