#ifndef PYAF_WRAPPER_TOOLS_NOISE_NOISE_HXX_
#define PYAF_WRAPPER_TOOLS_NOISE_NOISE_HXX_

#include "Tools/Noise/Event_probability.hpp"
#include "Tools/Noise/Noise.hpp"
#include "Tools/Noise/Received_optical_power.hpp"
#include "Tools/Noise/Sigma.hpp"

#include "internal/Wrapper/Tools/Noise/Noise.hpp"

namespace pyaf
{
namespace wrapper
{
template<typename R>
void
wrap_noise_internal(py::handle scope)
{
    using namespace aff3ct::tools;

    py::class_<Noise<R>>(scope,
                         class_name<R>("Noise").c_str(),
                         "Base class of the noises (Sigma, Event_probability, Received_optical_power).")
      .def_property_readonly("value", &Noise<R>::get_value, "float: value of the noise.")
      .def("set_value", &Noise<R>::set_value, "value"_a, "Set the value of the noise.")
      .def_property_readonly("type", &Noise<R>::get_type, "Noise_type: type of the noise.")
      .def_property_readonly("unity", &Noise<R>::get_unity, "str: unity of the value.")
      .def("is_set", &Noise<R>::is_set, "Return True if a value has been set.")
      .def("is_of_type", &Noise<R>::is_of_type, "type"_a, "Return True if the noise is of the given type.")
      .def("__float__", &Noise<R>::get_value)
      .def("__repr__",
           [](const Noise<R>& n)
           {
               return std::string(Noise<R>::type_to_str(n.get_type())) + "(" +
                      (n.is_set() ? std::to_string(n.get_value()) : std::string("unset")) + ")";
           });

    py::class_<Sigma<R>, Noise<R>>(scope,
                                   class_name<R>("Sigma").c_str(),
                                   "Gaussian noise: standard deviation, with the matching Eb/N0 and Es/N0 (dB).")
      .def(py::init<>())
      .def(py::init<R>(), "sigma"_a)
      .def(py::init<R, R, R>(), "sigma"_a, "ebn0"_a, "esn0"_a)
      .def_property_readonly("sigma", &Sigma<R>::get_sigma, "float: standard deviation.")
      .def_property_readonly("ebn0", &Sigma<R>::get_ebn0, "float: Eb/N0 (dB).")
      .def_property_readonly("esn0", &Sigma<R>::get_esn0, "float: Es/N0 (dB).")
      .def("set_values", &Sigma<R>::set_values, "sigma"_a, "ebn0"_a, "esn0"_a, "Set sigma, Eb/N0 and Es/N0.");

    py::class_<Event_probability<R>, Noise<R>>(scope,
                                               class_name<R>("Event_probability").c_str(),
                                               "Probability of an event (erasure, bit flip...).")
      .def(py::init<>())
      .def(py::init<R>(), "value"_a);

    py::class_<Received_optical_power<R>, Noise<R>>(scope,
                                                    class_name<R>("Received_optical_power").c_str(),
                                                    "Received optical power (optical channel).")
      .def(py::init<>())
      .def(py::init<R>(), "value"_a);
}
} // namespace wrapper
} // namespace pyaf

#endif // PYAF_WRAPPER_TOOLS_NOISE_NOISE_HXX_
