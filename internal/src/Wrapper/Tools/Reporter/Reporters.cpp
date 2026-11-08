#include "Module/Monitor/BFER/Monitor_BFER.hpp"
#include "Tools/Reporter/BFER/Reporter_BFER.hpp"
#include "Tools/Reporter/EXIT/Reporter_EXIT.hpp"
#include "Tools/Reporter/MI/Reporter_MI.hpp"
#include "Tools/Reporter/Noise/Reporter_noise.hpp"
#include "Tools/Reporter/Throughput/Reporter_throughput.hpp"

#include "internal/Wrapper/Tools/Reporter/Reporters.hpp"

using namespace aff3ct::tools;

namespace pyaf
{
namespace wrapper
{
template<typename B>
static void
wrap_reporter_bfer_internal(py::handle scope)
{
    using M = aff3ct::module::Monitor_BFER<B>;
    py::class_<Reporter_BFER<B>, spu::tools::Reporter>(
      scope,
      class_name<B>("Reporter_BFER").c_str(),
      R"pbdoc(Columns BE, FE, BER, FER of a BFER monitor, for ``streampu.Terminal_std``.

Args:
    monitor (aff3ct.mnt.Monitor_BFER): monitor (kept alive by the reporter).
)pbdoc")
      .def(py::init<const M&>(), "monitor"_a, py::keep_alive<1, 2>());
}

template<typename B, typename R>
static void
wrap_reporter_mi_internal(py::handle scope)
{
    using M = aff3ct::module::Monitor_MI<B, R>;
    py::class_<Reporter_MI<B, R>, spu::tools::Reporter>(
      scope,
      class_name<B, R>("Reporter_MI").c_str(),
      R"pbdoc(Columns TRIALS, MI, MIN, MAX of a mutual information monitor, for ``streampu.Terminal_std``.

Args:
    monitor (aff3ct.mnt.Monitor_MI): monitor (kept alive by the reporter).
)pbdoc")
      .def(py::init<const M&>(), "monitor"_a, py::keep_alive<1, 2>());
}

template<typename B, typename R>
static void
wrap_reporter_exit_internal(py::handle scope)
{
    using M = aff3ct::module::Monitor_EXIT<B, R>;
    py::class_<Reporter_EXIT<B, R>, spu::tools::Reporter>(
      scope,
      class_name<B, R>("Reporter_EXIT").c_str(),
      R"pbdoc(Columns SIG_A, I_A, I_E of an EXIT monitor, for ``streampu.Terminal_std``.

Args:
    monitor (aff3ct.mnt.Monitor_EXIT): monitor (kept alive by the reporter).
    noise_a (aff3ct.tools.Noise): noise of the a priori LLRs (kept alive by the reporter).
)pbdoc")
      .def(py::init<const M&, const Noise<>&>(), "monitor"_a, "noise_a"_a, py::keep_alive<1, 2>(),
           py::keep_alive<1, 3>());
}

template<typename R>
static void
wrap_reporter_noise_internal(py::handle scope)
{
    py::class_<Reporter_noise<R>, spu::tools::Reporter>(
      scope,
      class_name<R>("Reporter_noise").c_str(),
      R"pbdoc(Columns of a noise (Eb/N0 and Es/N0 for a Sigma, ...), for ``streampu.Terminal_std``.

Args:
    noise (aff3ct.tools.Noise): noise, read at each report (kept alive by the reporter).
    show_sigma (bool): add a sigma column.
)pbdoc")
      .def(py::init<const Noise<R>&, bool>(), "noise"_a, "show_sigma"_a = false, py::keep_alive<1, 2>());
}
} // namespace wrapper
} // namespace pyaf

void
pyaf::wrapper::wrap_reporters(py::handle scope)
{
    for_each_combo<gen::Tools_Reporter_BFER>(
      [&](auto c) { wrap_reporter_bfer_internal<typename decltype(c)::template at<0>>(scope); });
    for_each_combo<gen::Tools_Reporter_MI>(
      [&](auto c)
      { wrap_reporter_mi_internal<typename decltype(c)::template at<0>, typename decltype(c)::template at<1>>(scope); });
    for_each_combo<gen::Tools_Reporter_EXIT>(
      [&](auto c)
      { wrap_reporter_exit_internal<typename decltype(c)::template at<0>, typename decltype(c)::template at<1>>(scope); });
    for_each_combo<gen::Tools_Reporter_noise>(
      [&](auto c) { wrap_reporter_noise_internal<typename decltype(c)::template at<0>>(scope); });

    using T = Reporter_throughput<uint64_t>;
    py::class_<T, spu::tools::Reporter> thr(scope,
                                            "Reporter_throughput",
                                            R"pbdoc(Columns SIM_THR (Mb/s), ET/RT (elapsed time) and progress.

Args:
    monitor (aff3ct.mnt.Monitor_BFER): monitor whose analyzed frames give the throughput (kept alive).
)pbdoc");
    for_each_combo<gen::Module_Monitor_BFER>(
      [&](auto c)
      {
          using B = typename decltype(c)::template at<0>;
          thr.def(py::init<const aff3ct::module::Monitor_BFER<B>&>(), "monitor"_a, py::keep_alive<1, 2>());
      });
    thr.def("init", &T::init, "Restart the time measurement.");
}
