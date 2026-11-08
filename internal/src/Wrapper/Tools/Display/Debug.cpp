#include <fstream>
#include <memory>
#include <sstream>

#include "Tools/Algo/Histogram.hpp"
#include "Tools/Display/Dumper/Dumper.hpp"
#include "Tools/Display/Frame_trace/Frame_trace.hpp"

#include "internal/Wrapper/Tools/Display/Debug.hpp"

using namespace aff3ct::tools;

namespace pyaf
{
namespace wrapper
{
//! Read access to the counts of a Histogram (protected member).
template<typename R>
struct Histogram_access : public Histogram<R>
{
    static const std::map<int, size_t>& counts(const Histogram<R>& h)
    {
        return static_cast<const Histogram_access<R>&>(h).hist;
    }
};

template<typename R>
static void
wrap_histogram(py::handle scope)
{
    using H = Histogram<R>;
    py::class_<H>(scope,
                  class_name<R>("Histogram").c_str(),
                  R"pbdoc(Histogram of real values, rounded to ``precision`` decimals (one bin per rounded value).

>>> h = af.tools.Histogram(precision=2)
>>> h.add_values(np.random.randn(10000))
>>> x, counts = h.values                 # the rounded values and their counts
>>> h.dump("hist.txt", -4, 4)            # (x, y) lines, as AFF3CT (n_rung, norm_sum_to_1... set the format)
)pbdoc")
      .def(py::init<unsigned>(), "precision"_a = 3)
      .def(
        "add_values",
        [](H& h, py::array_t<R, py::array::c_style | py::array::forcecast> a)
        { h.add_values(a.data(), (size_t)a.size()); },
        "values"_a,
        "Add values (any array-like).")
      .def("add_value", py::overload_cast<const R&>(&H::add_value), "value"_a, "Add one value.")
      .def("reset", &H::reset, "Remove all the values.")
      .def_property_readonly("n_values", &H::get_n_values, "int: number of values added.")
      .def_property_readonly("hist_min", &H::get_hist_min, "float: smallest (rounded) value.")
      .def_property_readonly("hist_max", &H::get_hist_max, "float: largest (rounded) value.")
      .def_property_readonly(
        "values",
        [](const H& h)
        {
            const auto& c = Histogram_access<R>::counts(h);
            py::array_t<R> x((py::ssize_t)c.size());
            py::array_t<uint64_t> n((py::ssize_t)c.size());
            auto px = x.mutable_data();
            auto pn = n.mutable_data();
            for (auto& kv : c)
            {
                *px++ = h.uncalibrate_val(kv.first);
                *pn++ = (uint64_t)kv.second;
            }
            return py::make_tuple(x, n);
        },
        "tuple[numpy.ndarray, numpy.ndarray]: the rounded values (sorted) and their counts.")
      .def_property("n_rung",
                    py::overload_cast<>(&H::n_rung, py::const_),
                    py::overload_cast<unsigned>(&H::n_rung),
                    "int: number of abscissas of dump (0: every rounded value).")
      .def_property("norm_sum_to_1",
                    py::overload_cast<>(&H::norm_sum_to_1, py::const_),
                    py::overload_cast<bool>(&H::norm_sum_to_1),
                    "bool: dump a density (integral 1) instead of counts.")
      .def_property("cumul_vals",
                    py::overload_cast<>(&H::cumul_vals, py::const_),
                    py::overload_cast<bool>(&H::cumul_vals),
                    "bool: dump the cumulated values (CDF).")
      .def(
        "dump",
        [](const H& h, const std::string& path, py::object hmin, py::object hmax)
        {
            std::ofstream f(path);
            if (!f.is_open()) throw py::value_error("cannot open '" + path + "'");
            if (hmin.is_none() && hmax.is_none()) return h.dump(f);
            return h.dump(f,
                          hmin.is_none() ? h.get_hist_min() : hmin.cast<R>(),
                          hmax.is_none() ? h.get_hist_max() : hmax.cast<R>());
        },
        "path"_a,
        "hist_min"_a = py::none(),
        "hist_max"_a = py::none(),
        "Write the histogram in a text file, one (x, y) couple per line, between hist_min and hist_max.");
}

//! A Frame_trace writing in a string (std::cout is not shown by the notebooks).
struct Frame_trace_str
{
    std::ostringstream stream;
    Frame_trace<int32_t> trace;
    Frame_trace_str(int n_bits, int prec)
      : stream()
      , trace(n_bits, prec, stream)
    {
    }
    std::string take()
    {
        auto s = stream.str();
        stream.str("");
        stream.clear();
        return s;
    }
};

static std::vector<int32_t>
reference(const py::object& ref)
{
    if (ref.is_none()) return {};
    auto a = py::array_t<int32_t, py::array::c_style | py::array::forcecast>::ensure(ref);
    return std::vector<int32_t>(a.data(), a.data() + a.size());
}

template<typename D>
static std::string
display(Frame_trace_str& t, const py::array_t<D, py::array::c_style | py::array::forcecast>& a, unsigned row_width,
        const py::object& ref, int kind)
{
    std::vector<D> v(a.data(), a.data() + a.size());
    auto r = reference(ref);
    if (kind == 0)
        t.trace.display_bit_vector(v, row_width ? row_width : (unsigned)v.size(), r);
    else if (kind == 1)
        t.trace.display_real_vector(v, row_width ? row_width : (unsigned)v.size(), r);
    else
        t.trace.display_hex_vector(v, row_width ? row_width : (unsigned)v.size());
    return t.take();
}

template<typename D>
static void
add_display(py::class_<Frame_trace_str>& cls)
{
    using A = py::array_t<D, py::array::c_style | py::array::forcecast>;
    cls.def(
         "display_bit_vector",
         [](Frame_trace_str& t, const A& a, const py::object& ref, unsigned row_width)
         { return display<D>(t, a, row_width, ref, 0); },
         "vec"_a,
         "ref"_a = py::none(),
         "row_width"_a = 0)
      .def(
        "display_real_vector",
        [](Frame_trace_str& t, const A& a, const py::object& ref, unsigned row_width)
        { return display<D>(t, a, row_width, ref, 1); },
        "vec"_a,
        "ref"_a = py::none(),
        "row_width"_a = 0)
      .def(
        "display_hex_vector",
        [](Frame_trace_str& t, const A& a, unsigned row_width) { return display<D>(t, a, row_width, py::none(), 2); },
        "vec"_a,
        "row_width"_a = 0);
}

//! Pointer, size and dtype of a registered buffer (numpy array, or socket through its .numpy view).
template<typename T>
static void
register_typed(Dumper& d, const py::array& a, unsigned threshold, const std::string& ext, bool binary,
               unsigned n_frames, const std::vector<unsigned>& headers)
{
    d.register_data<T>(static_cast<const T*>(a.data()),
                       (unsigned)(a.size() / std::max(1u, n_frames)),
                       threshold,
                       ext,
                       binary,
                       n_frames,
                       headers);
}
} // namespace wrapper
} // namespace pyaf

void
pyaf::wrapper::wrap_debug_tools(py::handle scope)
{
    wrap_histogram<float>(scope); // header-only template: the R of the noises (float32, float64)
    wrap_histogram<double>(scope);

    py::class_<Frame_trace_str> ft(scope,
                                   "Frame_trace",
                                   R"pbdoc(Text view of frames (bits, reals, hexadecimal), errors highlighted against a reference.

The ``display_*`` methods return the text (with terminal colors): ``print`` it.

Args:
    n_bits (int): number of values displayed per frame (0: all).
    prec (int): number of characters of the reals.

>>> trace = af.tools.Frame_trace(n_bits=16)
>>> print(trace.display_bit_vector(dec["decode_siho::V_K"].numpy[0], ref=u.numpy[0]))
>>> print(trace.display_real_vector(llr.numpy[0], ref=x.numpy[0]))
)pbdoc");
    ft.def(py::init<int, int>(), "n_bits"_a = 0, "prec"_a = 5);
    add_display<int8_t>(ft);
    add_display<int16_t>(ft);
    add_display<int32_t>(ft);
    add_display<int64_t>(ft);
    add_display<float>(ft);
    add_display<double>(ft);

    py::class_<Dumper>(scope,
                       "Dumper",
                       R"pbdoc(Records frames that contain errors, then writes them in files (one file per registered buffer).

Register the buffers to record (sockets or arrays: their memory is read at each ``add``), then call
``add(n_errors, frame_id)`` after each frame, for instance from the callback of a BFER monitor; the frames with more
than ``add_threshold`` errors are copied. ``dump(base_path)`` writes ``base_path.<ext>`` for each buffer.

>>> dumper = af.tools.Dumper()
>>> dumper.register_data(u, file_ext="src")                  # sockets: kept alive by the dumper
>>> dumper.register_data(llr, file_ext="llr")
>>> mnt.record_callback_fe(lambda n_be, frame_id: dumper.add(n_be, frame_id))
>>> seq.exec()                                                # one thread: the callback is called from it
>>> dumper.dump("bad_frames")                                 # bad_frames.src, bad_frames.llr
)pbdoc")
      .def(py::init<>())
      .def(
        "register_data",
        [](Dumper& d, py::object data, unsigned add_threshold, const std::string& file_ext, bool binary_mode,
           unsigned n_frames, std::vector<unsigned> headers)
        {
            py::array a = py::hasattr(data, "numpy") ? data.attr("numpy").cast<py::array>() : data.cast<py::array>();
            if (!(a.flags() & py::array::c_style)) throw py::value_error("register_data: C-contiguous data expected");
            n_frames = std::max(1u, n_frames);
            if (a.ndim() == 2 && n_frames == 1) n_frames = (unsigned)a.shape(0);  // a socket: (n_frames, size)
            const auto dt = a.dtype();
            if (dt.is(py::dtype::of<int8_t>()))
                register_typed<int8_t>(d, a, add_threshold, file_ext, binary_mode, n_frames, headers);
            else if (dt.is(py::dtype::of<int16_t>()))
                register_typed<int16_t>(d, a, add_threshold, file_ext, binary_mode, n_frames, headers);
            else if (dt.is(py::dtype::of<int32_t>()))
                register_typed<int32_t>(d, a, add_threshold, file_ext, binary_mode, n_frames, headers);
            else if (dt.is(py::dtype::of<int64_t>()))
                register_typed<int64_t>(d, a, add_threshold, file_ext, binary_mode, n_frames, headers);
            else if (dt.is(py::dtype::of<float>()))
                register_typed<float>(d, a, add_threshold, file_ext, binary_mode, n_frames, headers);
            else if (dt.is(py::dtype::of<double>()))
                register_typed<double>(d, a, add_threshold, file_ext, binary_mode, n_frames, headers);
            else
                throw py::type_error("register_data: unsupported dtype");
        },
        "data"_a,
        "add_threshold"_a = 0,
        "file_ext"_a = "dump",
        "binary_mode"_a = false,
        "n_frames"_a = 1,
        "headers"_a = std::vector<unsigned>(),
        py::keep_alive<1, 2>(),
        "Register a socket or an array (C-contiguous, shape (n_frames, size) or (size,)) to record.")
      .def("add", &Dumper::add, "n_err"_a, "frame_id"_a = 0, "Record the frame if it has more than add_threshold errors.")
      .def("dump", &Dumper::dump, "base_path"_a, "Write base_path.<ext> for each registered buffer.")
      .def("clear", &Dumper::clear, "Forget the recorded frames.")
      .def("set_write_headers", &Dumper::set_write_headers, "write_headers"_a, "Write a header in the files.");
}
