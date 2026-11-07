/*!
 * \file
 * \brief Wrapper of aff3ct::module::Interleaver<D, T> (concrete module, header-only in AFF3CT).
 *
 * Python names: `Interleaver_int32_uint32`... (D = every dtype of factory::Interleaver::build, T = uint32, the
 * Interleaver_core<> of the factories); `aff3ct.itl.Interleaver(core)` builds the default instance (D = int32).
 */
#ifndef PYAF_WRAPPER_MODULE_INTERLEAVER_INTERLEAVER_HPP_
#define PYAF_WRAPPER_MODULE_INTERLEAVER_INTERLEAVER_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers aff3ct::module::Interleaver for every dtype combination of the factory.
void
wrap_interleaver(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_MODULE_INTERLEAVER_INTERLEAVER_HPP_
