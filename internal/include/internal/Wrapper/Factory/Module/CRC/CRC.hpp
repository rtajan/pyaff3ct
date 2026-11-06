/*!
 * \file
 * \brief Wrapper of aff3ct::factory::CRC (first factory, used to validate the transparent-factory mechanism).
 */
#ifndef PYAF_WRAPPER_FACTORY_MODULE_CRC_CRC_HPP_
#define PYAF_WRAPPER_FACTORY_MODULE_CRC_CRC_HPP_

#include "internal/Wrapper/Factory/Factory.hpp"

namespace pyaf
{
namespace wrapper
{
void
wrap_factory_crc(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_FACTORY_MODULE_CRC_CRC_HPP_
