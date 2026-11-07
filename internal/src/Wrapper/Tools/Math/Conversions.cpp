#include "Tools/general_utils.h"

#include "internal/Wrapper/Tools/Math/Conversions.hpp"

using namespace aff3ct::tools;

void
pyaf::wrapper::wrap_conversions(py::handle scope)
{
    auto m = py::reinterpret_borrow<py::module_>(scope);
    m.def("sigma_to_esn0",
          &sigma_to_esn0<double>,
          "sigma"_a,
          "upsample_factor"_a = 1,
          "Es/N0 (dB) of a Gaussian noise of standard deviation sigma.");
    m.def("esn0_to_sigma",
          &esn0_to_sigma<double>,
          "esn0"_a,
          "upsample_factor"_a = 1,
          "Standard deviation of the Gaussian noise of Es/N0 (dB).");
    m.def("esn0_to_ebn0",
          &esn0_to_ebn0<double>,
          "esn0"_a,
          "code_rate"_a = 1.,
          "bps"_a = 1,
          "Eb/N0 (dB) from Es/N0 (dB), for a code rate and a number of bits per symbol.");
    m.def("ebn0_to_esn0",
          &ebn0_to_esn0<double>,
          "ebn0"_a,
          "code_rate"_a = 1.,
          "bps"_a = 1,
          "Es/N0 (dB) from Eb/N0 (dB), for a code rate and a number of bits per symbol.");
}
