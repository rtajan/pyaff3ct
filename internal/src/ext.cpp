/*!
 * \file
 * \brief Entry point of the compiled extension `aff3ct._ext`.
 *
 * Python sub-modules = AFF3CT factory prefixes (crc, chn, cst, dec, enc, ext, mdm, mnt, pct, qnt...), plus
 * `interfaces`, `tools` and `factory`.
 */
#include "internal/internal.hpp"

#include "internal/Wrapper/Factory/Factory.hpp"
#include "internal/Wrapper/Factory/Module/CRC/CRC.hpp"
#include "internal/Wrapper/Module/Bases.hpp"
#include "internal/Wrapper/Testing/Testing.hpp"
#include "internal/Wrapper/Tools/Interface/Interfaces.hpp"
#include "internal/Wrapper/Tools/Noise/Noise.hpp"

#include "Tools/version.h"

using namespace pyaf::wrapper;

PYBIND11_MODULE(_ext, m, py::mod_gil_not_used())
{
    // The base classes (Module, Stateful, Task, Socket, spu::tools::Interface_*...) are those of pystreampu: they
    // must be registered before ours.
    m.attr("_streampu") = py::module_::import("streampu");
    // This extension links its own copy of the static StreamPU library (official model of the pystreampu
    // extensions): enable the automatic allocation of the task sockets here too, as streampu does for its modules.
    spu::tools::Buffer_allocator::set_task_autoalloc(true);

#ifdef PYAF_HAS_STREAMPU_DOWNCAST_REGISTRY
    m.attr("HAS_STREAMPU_DOWNCAST_REGISTRY") = true;
#else
    m.attr("HAS_STREAMPU_DOWNCAST_REGISTRY") = false;
#endif
    m.attr("AFF3CT_VERSION") = aff3ct::tools::version();
    m.attr("AFF3CT_GIT_HASH") = aff3ct::tools::sha1();

    auto itf = m.def_submodule("interfaces", "AFF3CT interfaces (frozen bits, noise, trellis...).");
    auto tools = m.def_submodule("tools", "AFF3CT tools.");
    wrap_noise(tools);
    wrap_interfaces(itf);

    wrap_crc(m.def_submodule("crc", "CRCs."));
    wrap_channel(m.def_submodule("chn", "Channels."));
    wrap_coset(m.def_submodule("cst", "Cosets."));
    wrap_decoder(m.def_submodule("dec", "Decoders."));
    wrap_encoder(m.def_submodule("enc", "Encoders."));
    wrap_extractor(m.def_submodule("ext", "Extractors."));
    wrap_modem(m.def_submodule("mdm", "Modems."));
    wrap_monitor(m.def_submodule("mnt", "Monitors."));
    wrap_puncturer(m.def_submodule("pct", "Puncturers."));
    wrap_quantizer(m.def_submodule("qnt", "Quantizers."));

    auto fac = m.def_submodule("factory", "AFF3CT factories (advanced use: command-line parity, parameters).");
    wrap_factory(fac);
    wrap_factory_crc(fac);

    wrap_testing(m.def_submodule("_testing", "Helpers of the test suite (not part of the public API)."));
}
