#include "Tools/Interleaver/Interleaver_core.hpp"
#include "Tools/Interleaver/ARP/Interleaver_core_ARP_DVB_RCS1.hpp"
#include "Tools/Interleaver/ARP/Interleaver_core_ARP_DVB_RCS2.hpp"
#include "Tools/Interleaver/CCSDS/Interleaver_core_CCSDS.hpp"
#include "Tools/Interleaver/Column_row/Interleaver_core_column_row.hpp"
#include "Tools/Interleaver/Golden/Interleaver_core_golden.hpp"
#include "Tools/Interleaver/LTE/Interleaver_core_LTE.hpp"
#include "Tools/Interleaver/NO/Interleaver_core_NO.hpp"
#include "Tools/Interleaver/Random/Interleaver_core_random.hpp"
#include "Tools/Interleaver/Random_column/Interleaver_core_random_column.hpp"
#include "Tools/Interleaver/Row_column/Interleaver_core_row_column.hpp"
#include "Tools/Interleaver/User/Interleaver_core_user.hpp"

#include "internal/Wrapper/Tools/Interleaver/Interleaver_core.hpp"

using namespace aff3ct::tools;

namespace pyaf
{
namespace wrapper
{
template<typename T>
static void
wrap_interleaver_core_base(py::handle scope)
{
    using I = Interleaver_core<T>;
    py::class_<I, spu::tools::Interface_set_seed, spu::tools::Interface_get_set_n_frames>(
      scope,
      class_name<T>("Interleaver_core").c_str(),
      R"pbdoc(Base class of the interleaver cores: lookup table of a permutation (``aff3ct.itl.Interleaver`` applies it).

The output position ``i`` of the interleaving reads the input position ``lut[i]``.
)pbdoc")
      .def_property_readonly(
        "lut", [](const I& i) { return to_numpy(i.get_lut()); }, "numpy.ndarray: lookup table (a copy), one per frame.")
      .def_property_readonly(
        "lut_inv",
        [](const I& i) { return to_numpy(i.get_lut_inv()); },
        "numpy.ndarray: inverse lookup table (a copy).")
      .def_property_readonly("size", &I::get_size, "int: number of interleaved elements per frame.")
      .def_property_readonly("name", &I::get_name, "str: name of the interleaver (e.g. 'Random').")
      .def("is_uniform", &I::is_uniform, "Return True if a new permutation is drawn for each frame.")
      .def("refresh", &I::refresh, "Draw a new permutation (uniform interleavers).")
      .def("reinitialize", &I::reinitialize, "Come back to the initial permutation (seed included).")
      .def("__len__", &I::get_size);
}

template<typename T>
static void
wrap_interleaver_core_children(py::handle scope)
{
    using B = Interleaver_core<T>;
    py::class_<Interleaver_core_NO<T>, B>(scope, class_name<T>("Interleaver_core_NO").c_str(), "Identity permutation.")
      .def(py::init<int>(), "size"_a);
    py::class_<Interleaver_core_random<T>, B>(
      scope, class_name<T>("Interleaver_core_random").c_str(), "Pseudo-random permutation (Mersenne Twister).")
      .def(py::init<int, int, bool>(), "size"_a, "seed"_a = 0, "uniform"_a = false);
    py::class_<Interleaver_core_random_column<T>, B>(scope,
                                                     class_name<T>("Interleaver_core_random_column").c_str(),
                                                     "Pseudo-random permutation of each of the n_cols columns.")
      .def(py::init<int, int, int, bool>(), "size"_a, "n_cols"_a, "seed"_a = 0, "uniform"_a = false);
    py::class_<Interleaver_core_golden<T>, B>(
      scope, class_name<T>("Interleaver_core_golden").c_str(), "Golden-ratio permutation (dithered).")
      .def(py::init<int, int, bool>(), "size"_a, "seed"_a = 0, "uniform"_a = false);
    py::class_<Interleaver_core_row_column<T>, B>(
      scope,
      class_name<T>("Interleaver_core_row_column").c_str(),
      "Written row by row, read column by column (read_order: 'TOP_LEFT', 'TOP_RIGHT', 'BOTTOM_LEFT', 'BOTTOM_RIGHT').")
      .def(py::init<int, int, const std::string&>(), "size"_a, "n_cols"_a, "read_order"_a = "TOP_LEFT");
    py::class_<Interleaver_core_column_row<T>, B>(
      scope,
      class_name<T>("Interleaver_core_column_row").c_str(),
      "Written column by column, read row by row (read_order: 'TOP_LEFT', 'TOP_RIGHT', 'BOTTOM_LEFT', 'BOTTOM_RIGHT').")
      .def(py::init<int, int, const std::string&>(), "size"_a, "n_cols"_a, "read_order"_a = "TOP_LEFT");
    py::class_<Interleaver_core_user<T>, B>(
      scope,
      class_name<T>("Interleaver_core_user").c_str(),
      "Permutation(s) read from a file (one or several lookup tables, see the AFF3CT documentation).")
      .def(py::init<int, const std::string&>(), "size"_a, "filename"_a);
    py::class_<Interleaver_core_ARP_DVB_RCS1<T>, B>(
      scope, class_name<T>("Interleaver_core_ARP_DVB_RCS1").c_str(), "Almost regular permutation of DVB-RCS1.")
      .def(py::init<int>(), "size"_a);
    py::class_<Interleaver_core_ARP_DVB_RCS2<T>, B>(
      scope, class_name<T>("Interleaver_core_ARP_DVB_RCS2").c_str(), "Almost regular permutation of DVB-RCS2.")
      .def(py::init<int>(), "size"_a);
}

template<typename T>
static void
wrap_interleaver_core_LTE_CCSDS(py::handle scope)
{
    using B = Interleaver_core<T>;
    py::class_<Interleaver_core_LTE<T>, B>(
      scope, class_name<T>("Interleaver_core_LTE").c_str(), "Quadratic permutation polynomial interleaver of LTE.")
      .def(py::init<int>(), "size"_a);
    py::class_<Interleaver_core_CCSDS<T>, B>(
      scope, class_name<T>("Interleaver_core_CCSDS").c_str(), "Interleaver of the CCSDS turbo codes.")
      .def(py::init<int>(), "size"_a);
}
} // namespace wrapper
} // namespace pyaf

void
pyaf::wrapper::wrap_interleaver_core(py::handle scope)
{
    for_each_combo<gen::Tools_Interleaver_core>(
      [&](auto c) { wrap_interleaver_core_base<typename decltype(c)::template at<0>>(scope); });
    for_each_combo<gen::Tools_Interleaver_core_NO>(
      [&](auto c) { wrap_interleaver_core_children<typename decltype(c)::template at<0>>(scope); });
    for_each_combo<gen::Tools_Interleaver_core_LTE>(
      [&](auto c) { wrap_interleaver_core_LTE_CCSDS<typename decltype(c)::template at<0>>(scope); });
}
