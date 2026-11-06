#include "internal/Wrapper/Tools/Noise/Noise.hpp"

void
pyaf::wrapper::wrap_noise(py::handle scope)
{
    using aff3ct::tools::Noise_type;
    py::enum_<Noise_type>(scope, "Noise_type", "Type of a noise.")
      .value("SIGMA", Noise_type::SIGMA, "Standard deviation of a Gaussian noise.")
      .value("ROP", Noise_type::ROP, "Received optical power.")
      .value("EP", Noise_type::EP, "Event probability.");

    for_each_combo<gen::Tools_Noise>([&](auto c) { wrap_noise_internal<typename decltype(c)::template at<0>>(scope); });
}
