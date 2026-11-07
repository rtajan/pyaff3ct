#include "Module/Monitor/Monitor.hpp"
#include "Module/Monitor/BFER/Monitor_BFER.hpp"

#include "internal/Module/Monitor/BFER_AR/Monitor_BFER_AR.hpp"
#include "internal/Wrapper/Module/Monitor/Monitor.hpp"

namespace pyaf
{
namespace wrapper
{
template<typename B>
static void
wrap_monitor_bfer_internal(py::handle scope)
{
    using M = aff3ct::module::Monitor_BFER<B>;
    using aff3ct::module::Monitor;
    py::class_<M, Monitor>(scope,
                           class_name<B>("Monitor_BFER").c_str(),
                           R"pbdoc(Bit and frame error rate monitor.

Tasks: ``check_errors(U, V)`` (``U``: reference bits, ``V``: decoded bits, compared as booleans) and
``check_errors2`` (also outputs the counters). ``is_done()`` is True once ``max_fe`` frame errors (or
``max_n_frames`` frames, if not 0) are reached.

Args:
    K (int): number of bits per frame.
    max_fe (int): number of frame errors to stop.
    max_n_frames (int): number of frames to stop (0: no limit).
    count_unknown_values (bool): count the erased bits as errors.
)pbdoc")
      .def(py::init<int, unsigned, unsigned, bool>(),
           "K"_a,
           "max_fe"_a,
           "max_n_frames"_a = 0,
           "count_unknown_values"_a = false)
      .def_property_readonly("K", &M::get_K, "int: number of bits per frame.")
      .def_property_readonly("max_fe", &M::get_max_fe, "int: frame errors to stop.")
      .def_property_readonly("max_n_frames", &M::get_max_n_frames, "int: frames to stop (0: no limit).")
      .def_property_readonly(
        "count_unknown_values", &M::get_count_unknown_values, "bool: the erased bits are counted as errors.")
      .def_property_readonly("n_analyzed_frames", &M::get_n_analyzed_fra, "int: number of checked frames.")
      .def_property_readonly("n_fe", &M::get_n_fe, "int: number of frame errors.")
      .def_property_readonly("n_be", &M::get_n_be, "int: number of bit errors.")
      .def_property_readonly("fer", &M::get_fer, "float: frame error rate.")
      .def_property_readonly("ber", &M::get_ber, "float: bit error rate.")
      .def("fe_limit_achieved", &M::fe_limit_achieved, "Return True if max_fe frame errors are reached.")
      .def("frame_limit_achieved", &M::frame_limit_achieved, "Return True if max_n_frames frames are reached.")
      .def("disable_is_done", &M::disable_is_done, "no_is_done"_a, "Make is_done() always False (or not).")
      .def("collect",
           py::overload_cast<const M&, bool>(&M::collect),
           "monitor"_a,
           "fully"_a = false,
           "Add the counters of another monitor (e.g. the clones of a Sequence).")
      .def("copy",
           py::overload_cast<const M&, bool>(&M::copy),
           "monitor"_a,
           "fully"_a = false,
           "Copy the counters of another monitor.")
      .def(
        "__iadd__", [](M& a, const M& b) -> M& { return a += b; }, py::return_value_policy::reference_internal)
      .def("record_callback_fe",
           &M::record_callback_fe,
           "callback"_a,
           "Call callback(n_bit_errors, frame_id) at each frame error; returns an id (unrecord_callback_fe).")
      .def("record_callback_check", &M::record_callback_check, "callback"_a, "Call callback() after each check.")
      .def("record_callback_fe_limit_achieved",
           &M::record_callback_fe_limit_achieved,
           "callback"_a,
           "Call callback() when max_fe is reached.")
      .def("unrecord_callback_fe", &M::unrecord_callback_fe, "id"_a)
      .def("unrecord_callback_check", &M::unrecord_callback_check, "id"_a)
      .def("unrecord_callback_fe_limit_achieved", &M::unrecord_callback_fe_limit_achieved, "id"_a);
    add_module_class<M>();

    using AR = pyaf::module::Monitor_BFER_AR<B>;
    py::class_<AR, M>(scope,
                      class_name<B>("Monitor_BFER_AR").c_str(),
                      R"pbdoc(BFER monitor whose clones share their counters (pyaff3ct only, temporary).

In a multi-threaded ``streampu.Sequence`` every thread runs a clone of the monitor; with ``Monitor_BFER`` each clone
counts its own errors and the sequence stops as soon as *one* of them reaches ``max_fe``. The clones of a
``Monitor_BFER_AR`` add their frames to shared totals, which they and the original monitor report: the sequence stops
when the *total* reaches ``max_fe``, and the original monitor (given to ``Reporter_BFER``...) shows the totals,
without collecting the clones. ``reset()`` resets the totals.

Same arguments, tasks and accessors as ``Monitor_BFER`` (it is one).

>>> mnt = af.mnt.Monitor_BFER_AR(K, max_fe=100)
>>> mnt.check_errors(u, v)                         # binds the chain
>>> spu.Sequence(mnt["check_errors::status"], n_threads=8).exec()
>>> mnt.fer                                        # totals of the 8 threads
)pbdoc")
      .def(py::init<int, unsigned, unsigned, bool>(),
           "K"_a,
           "max_fe"_a,
           "max_n_frames"_a = 0,
           "count_unknown_values"_a = false)
      .def("is_shared_with",
           &AR::is_shared_with,
           "monitor"_a,
           "Return True if the monitor shares its counters with this one (clone or original).");
    add_module_class<AR>();
}
} // namespace wrapper
} // namespace pyaf

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

    for_each_combo<gen::Module_Monitor_BFER>(
      [&](auto c) { wrap_monitor_bfer_internal<typename decltype(c)::template at<0>>(scope); });
}
