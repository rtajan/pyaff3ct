/*!
 * \file
 * \brief Helpers of the test suite (`aff3ct._ext._testing`): they exercise the pyaff3ct casters directly, before any
 *        module that uses them is wrapped. Not part of the public API.
 */
#ifndef PYAF_WRAPPER_TESTING_TESTING_HPP_
#define PYAF_WRAPPER_TESTING_TESTING_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers the test helpers in `scope`.
void
wrap_testing(py::module_ scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_TESTING_TESTING_HPP_
