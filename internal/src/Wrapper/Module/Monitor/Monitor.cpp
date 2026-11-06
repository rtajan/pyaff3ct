#include "Module/Monitor/Monitor.hpp"

#include "internal/Wrapper/Module/Monitor/Monitor.hpp"

void
pyaf::wrapper::wrap_monitor(py::handle scope)
{
    using aff3ct::module::Monitor;
    py::class_<Monitor, spu::module::Stateful, spu::tools::Interface_reset, spu::tools::Interface_is_done>(
      scope,
      "Monitor",
      R"pbdoc(Base class of the monitors (BFER, EXIT, MI).

``is_done()`` (from ``Interface_is_done``) becomes True when the stop criterion is reached, which stops the
execution of a ``streampu.Sequence``.
)pbdoc")
      .def("clear_callbacks", &Monitor::clear_callbacks, "Remove the callbacks registered on the monitor.");
    add_module_class<Monitor>();
}
