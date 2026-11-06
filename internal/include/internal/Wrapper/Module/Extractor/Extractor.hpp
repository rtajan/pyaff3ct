/*!
 * \file
 * \brief Wrapper of the abstract base aff3ct::module::Extractor (see Bases.hpp).
 */
#ifndef PYAF_WRAPPER_MODULE_EXTRACTOR_EXTRACTOR_HPP_
#define PYAF_WRAPPER_MODULE_EXTRACTOR_EXTRACTOR_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers aff3ct::module::Extractor for every dtype combination compiled by AFF3CT.
void
wrap_extractor(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_MODULE_EXTRACTOR_EXTRACTOR_HPP_
