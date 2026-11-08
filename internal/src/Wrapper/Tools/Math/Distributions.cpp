#include "Tools/Math/Distribution/Distribution.hpp"
#include "Tools/Math/Distribution/Distributions.hpp"

#include "internal/Generated/instantiations.hpp"
#include "internal/Wrapper/Tools/Math/Distributions.hpp"

using namespace aff3ct::tools;

namespace pyaf
{
namespace wrapper
{
template<typename R>
static py::array_t<R>
to_array(const std::vector<R>& v)
{
    return py::array_t<R>((py::ssize_t)v.size(), v.data());
}

template<typename R>
static py::list
to_arrays(const std::vector<std::vector<R>>& v)
{
    py::list l;
    for (auto& x : v)
        l.append(to_array(x));
    return l;
}

template<typename R>
static void
wrap_distributions_internal(py::handle scope)
{
    using D = Distribution<R>;
    py::class_<D>(scope,
                  class_name<R>("Distribution").c_str(),
                  "Probability density of the received values for one noise value (read by Distributions).")
      .def_property_readonly(
        "pdf_x", [](const D& d) { return to_array(d.get_pdf_x()); }, "numpy.ndarray: abscissas of the densities.")
      .def_property_readonly(
        "pdf_y",
        [](const D& d) { return to_arrays(d.get_pdf_y()); },
        "list[numpy.ndarray]: densities, one per transmitted value (0, 1).")
      .def_property_readonly(
        "pdf_norm_y",
        [](const D& d) { return to_arrays(d.get_pdf_norm_y()); },
        "list[numpy.ndarray]: normalized densities.")
      .def_property_readonly(
        "cdf_x", [](const D& d) { return to_arrays(d.get_cdf_x()); }, "list[numpy.ndarray]: abscissas of the CDFs.")
      .def_property_readonly(
        "cdf_y", [](const D& d) { return to_arrays(d.get_cdf_y()); }, "list[numpy.ndarray]: CDFs.");

    using Ds = Distributions<R>;
    py::class_<Ds>(scope,
                   class_name<R>("Distributions").c_str(),
                   R"pbdoc(Noise distributions read from a file, one per noise value (received optical power, ROP).

Used by the optical channel and the OOK optical modem (``af.chn.channel(N, dist, type="OPTICAL")``,
``af.mdm.modem(N, None, dist, type="OOK", channel_type="OPTICAL")``), that keep it alive.

>>> dist = af.tools.Distributions("conf/chn/optical_channel.dist")
>>> dist.noise_range                  # ROP values (dB) of the file
>>> dist.read_distribution(-45.0)     # load the distribution of a ROP (done by the modules when needed)
)pbdoc")
      .def(py::init<const std::string&, Distribution_mode>(),
           "path"_a,
           py::arg_v("mode", Distribution_mode::SUMMATION, "aff3ct.tools.Distribution_mode.SUMMATION"),
           "Read the noise values of the file (the distributions are read on demand).")
      .def_property_readonly(
        "noise_range",
        [](const Ds& d) { return to_array(d.get_noise_range()); },
        "numpy.ndarray: noise values (ROP) of the file.")
      .def("has_distribution", &Ds::has_distribution, "noise"_a, "True if the distribution of this noise is loaded.")
      .def("read_distribution", &Ds::read_distribution, "noise"_a, "Load the distribution of a noise value.")
      .def("get_distribution",
           &Ds::get_distribution,
           "noise"_a,
           py::return_value_policy::reference_internal,
           "Distribution of a noise value (read_distribution first).");
}
} // namespace wrapper
} // namespace pyaf

void
pyaf::wrapper::wrap_distributions(py::handle scope)
{
    py::enum_<Distribution_mode>(scope, "Distribution_mode", "How the CDFs are computed from the densities.")
      .value("INTERPOLATION", Distribution_mode::INTERPOLATION)
      .value("SUMMATION", Distribution_mode::SUMMATION);
    for_each_combo<gen::Tools_Distributions>(
      [&](auto c) { wrap_distributions_internal<typename decltype(c)::template at<0>>(scope); });
}
