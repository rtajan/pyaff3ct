/*!
 * \file
 * \brief Common includes and definitions of the pyaff3ct extension (aff3ct._ext).
 *
 * Every wrapper includes this header first: it brings pybind11 (with the pyaff3ct casters), StreamPU and the helpers
 * of internal/Common/Tools. AFF3CT headers are included by each wrapper (only the ones it needs, to keep the
 * compilation time reasonable).
 */
#ifndef PYAF_INTERNAL_HPP_
#define PYAF_INTERNAL_HPP_

#include <string>

#include <pybind11/functional.h>
#include <pybind11/iostream.h>
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <streampu.hpp>

#include "internal/Common/Tools/casters.hpp"
#include "internal/Common/Tools/combos.hpp"
#include "internal/Common/Tools/dtypes.hpp"
#include "internal/Generated/instantiations.hpp"

namespace py = pybind11;
using namespace py::literals;

namespace pyaf
{
namespace wrapper
{
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_INTERNAL_HPP_
