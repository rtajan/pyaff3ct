/*!
 * \file
 * \brief Wrappers of the abstract bases of the AFF3CT modules (Plan.md, rule R2).
 *
 * The bases are bound without constructor, once per dtype combination compiled by AFF3CT
 * (`Encoder_int8` ... `Encoder_int64`, `Decoder_SIHO_int32_float32`...). They carry the accessors shared by every
 * child; tasks and sockets need no binding: they are reached through the pystreampu `Module` interface
 * (`enc.encode(u)`, `enc["encode::U_K"]`).
 *
 * One header/implementation pair per AFF3CT domain, mirroring include/Module/<Domain>/<Domain>.hpp.
 */
#ifndef PYAF_WRAPPER_MODULE_BASES_HPP_
#define PYAF_WRAPPER_MODULE_BASES_HPP_

#include "internal/Wrapper/Module/CRC/CRC.hpp"
#include "internal/Wrapper/Module/Channel/Channel.hpp"
#include "internal/Wrapper/Module/Coset/Coset.hpp"
#include "internal/Wrapper/Module/Decoder/Decoder.hpp"
#include "internal/Wrapper/Module/Encoder/Encoder.hpp"
#include "internal/Wrapper/Module/Extractor/Extractor.hpp"
#include "internal/Wrapper/Module/Modem/Modem.hpp"
#include "internal/Wrapper/Module/Monitor/Monitor.hpp"
#include "internal/Wrapper/Module/Puncturer/Puncturer.hpp"
#include "internal/Wrapper/Module/Quantizer/Quantizer.hpp"

#endif // PYAF_WRAPPER_MODULE_BASES_HPP_
