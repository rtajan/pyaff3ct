/*!
 * \file
 * \brief Wrappers of the AFF3CT tools: Sparse_matrix (+ Matrix enums).
 */
#ifndef PYAF_WRAPPER_TOOLS_ALGO_SPARSE_MATRIX_HPP_
#define PYAF_WRAPPER_TOOLS_ALGO_SPARSE_MATRIX_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers Matrix (enums Way, Sort, Origin) and Sparse_matrix.
void
wrap_sparse_matrix(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_TOOLS_ALGO_SPARSE_MATRIX_HPP_
