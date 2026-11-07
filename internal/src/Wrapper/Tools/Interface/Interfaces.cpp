#include "internal/Wrapper/Tools/Interface/Interfaces.hpp"

#include "Tools/Interface/Interface_get_set_dynamic_frozen_bits.hpp"
#include "Tools/Interface/Interface_get_set_frozen_bits.hpp"
#include "Tools/Interface/Interface_get_set_noise.hpp"
#include "Tools/Interface/Interface_get_set_pretransform.hpp"
#include "Tools/Interface/Interface_get_trellis.hpp"
#include "Tools/Interface/Interface_notify_noise_update.hpp"
#include "Tools/Noise/Noise.hpp"

using namespace aff3ct::tools;

void
pyaf::wrapper::wrap_interface_get_set_frozen_bits(py::handle scope)
{
    using I = Interface_get_set_frozen_bits;
    py::class_<I>(
      scope, "Interface_get_set_frozen_bits", "Interface of the objects that use frozen bits (polar codes).")
      .def_property_readonly(
        "frozen_bits", &I::get_frozen_bits, "numpy.ndarray[bool]: frozen bits (True = frozen), one per codeword bit.")
      .def("set_frozen_bits", &I::set_frozen_bits, "frozen_bits"_a, "Set the frozen bits (array-like of bool).");
}

void
pyaf::wrapper::wrap_interface_get_set_dynamic_frozen_bits(py::handle scope)
{
    using I = Interface_get_set_dynamic_frozen_bits;
    py::class_<I>(scope,
                  "Interface_get_set_dynamic_frozen_bits",
                  "Interface of the objects that use dynamic frozen bits (pre-transformed polar codes).")
      .def_property_readonly(
        "dynamic_frozen_bits", &I::get_dynamic_frozen_bits, "numpy.ndarray[bool]: dynamic frozen bits.")
      .def("set_dynamic_frozen_bits", &I::set_dynamic_frozen_bits, "frozen_bits"_a, "Set the dynamic frozen bits.");
}

void
pyaf::wrapper::wrap_interface_get_set_pretransform(py::handle scope)
{
    using I = Interface_get_set_pretransform;
    py::class_<I>(scope,
                  "Interface_get_set_pretransform",
                  "Interface of the objects that use a pre-transformation (pre-transformed polar codes).")
      .def_property_readonly(
        "pretransform",
        &I::get_pretransform,
        "dict[int, list[int]]: pre-transformation (bit index -> indices of the bits it depends on).")
      .def("set_pretransform", &I::set_pretransform, "pretransform"_a, "Set the pre-transformation.");
}

void
pyaf::wrapper::wrap_interface_get_trellis(py::handle scope)
{
    using I = Interface_get_trellis;
    py::class_<I>(
      scope, "Interface_get_trellis", "Interface of the objects that provide a trellis (convolutional codes).")
      .def_property_readonly("trellis", &I::get_trellis, "list[list[int]]: trellis of the code.");
}

void
pyaf::wrapper::wrap_interface_get_set_noise(py::handle scope)
{
    using I = Interface_get_set_noise;
    py::class_<I>(scope, "Interface_get_set_noise", "Interface of the objects that depend on the noise (tools.Noise).")
      .def_property_readonly(
        "noise", &I::get_noise, py::return_value_policy::reference_internal, "aff3ct.tools.Noise: current noise.")
      .def("set_noise",
           &I::set_noise,
           "noise"_a,
           py::keep_alive<1, 2>(),
           "Set the noise (aff3ct.tools.Noise_float32, kept alive: the object stores a reference).");
}

void
pyaf::wrapper::wrap_interface_notify_noise_update(py::handle scope)
{
    using I = Interface_notify_noise_update;
    py::class_<I>(
      scope, "Interface_notify_noise_update", "Interface of the objects that must be notified when the noise changes.")
      .def("notify_noise_update", &I::notify_noise_update, "Notify the object that the noise has been updated.");
}

void
pyaf::wrapper::wrap_interfaces(py::handle scope)
{
    wrap_interface_get_set_frozen_bits(scope);
    wrap_interface_get_set_dynamic_frozen_bits(scope);
    wrap_interface_get_set_pretransform(scope);
    wrap_interface_get_trellis(scope);
    wrap_interface_get_set_noise(scope);
    wrap_interface_notify_noise_update(scope);
}
