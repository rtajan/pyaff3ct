/*!
 * \file
 * \brief Wrappers of aff3ct::tools::Frozenbits_generator and of its children (GA_Arikan, BEC, file).
 */
#ifndef PYAF_WRAPPER_TOOLS_CODE_FROZENBITS_GENERATOR_HPP_
#define PYAF_WRAPPER_TOOLS_CODE_FROZENBITS_GENERATOR_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers Frozenbits_generator, Frozenbits_generator_GA_Arikan, _BEC and _file (after the interfaces).
void
wrap_frozenbits_generator(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_TOOLS_CODE_FROZENBITS_GENERATOR_HPP_
