/*!
 * \file
 * \brief Wrappers of the AFF3CT tools: LDPC matrix readers and writers (AList, QC, LDPC_matrix_handler).
 */
#ifndef PYAF_WRAPPER_TOOLS_CODE_LDPC_HPP_
#define PYAF_WRAPPER_TOOLS_CODE_LDPC_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers AList, QC and LDPC_matrix_handler (static methods, file paths).
void
wrap_ldpc_tools(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_TOOLS_CODE_LDPC_HPP_
