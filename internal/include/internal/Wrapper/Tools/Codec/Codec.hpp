/*!
 * \file
 * \brief Wrappers of aff3ct::tools::Codec<B, Q> (HIHO, SIHO, SISO) and of the codecs of every code family.
 *
 * A codec is built by its factory (`aff3ct.codec.polar(K, N_cw, ...)`, see aff3ct/codec.py) and owns the modules it
 * builds and connects (encoder, decoders, puncturer, extractor, interleaver): they are exposed as properties that
 * keep the codec alive.
 */
#ifndef PYAF_WRAPPER_TOOLS_CODEC_CODEC_HPP_
#define PYAF_WRAPPER_TOOLS_CODEC_CODEC_HPP_

#include "internal/internal.hpp"

namespace pyaf
{
namespace wrapper
{
//! Registers the codecs for every dtype combination (after the modules, the interfaces and the tools they return).
void
wrap_codecs(py::handle scope);
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_TOOLS_CODEC_CODEC_HPP_
