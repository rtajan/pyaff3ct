#include "Module/Channel/Channel.hpp"

#include "internal/Wrapper/Module/Channel/Channel.hpp"

namespace pyaf
{
namespace wrapper
{
template<typename R>
static void
wrap_channel_internal(py::handle scope)
{
    using C = aff3ct::module::Channel<R>;
    py::class_<C, spu::module::Stateful, spu::tools::Interface_set_seed>(scope,
                                                                         class_name<R>("Channel").c_str(),
                                                                         R"pbdoc(Base class of the channels.

Tasks: ``add_noise(CP, X_N -> Y_N)``, ``add_noise_wg(CP, X_N -> H_N, Y_N)``; ``CP`` is the channel parameter
(sigma, event probability or received optical power, as a 1-element float32 socket).
)pbdoc")
      .def_property_readonly("N", &C::get_N, "int: frame size.")
      .def_property_readonly(
        "noised_data",
        [](const C& c) { return to_numpy(c.get_noised_data()); },
        "numpy.ndarray: last noise drawn by the channel (copy).");
}
} // namespace wrapper
} // namespace pyaf

void
pyaf::wrapper::wrap_channel(py::handle scope)
{
    for_each_combo<gen::Module_Channel>([&](auto c)
                                        { wrap_channel_internal<typename decltype(c)::template at<0>>(scope); });
}
