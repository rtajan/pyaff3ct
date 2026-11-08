#include <complex>

#include <pybind11/complex.h>

#include "Tools/Constellation/Constellation.hpp"
#include "Tools/Constellation/PAM/Constellation_PAM.hpp"
#include "Tools/Constellation/PSK/Constellation_PSK.hpp"
#include "Tools/Constellation/QAM/Constellation_QAM.hpp"
#include "Tools/Constellation/User/Constellation_user.hpp"

#include "internal/Wrapper/Tools/Constellation/Constellation.hpp"

using namespace aff3ct::tools;

namespace pyaf
{
namespace wrapper
{
//! Gives access to the protected constructor Constellation(symbols, name) of AFF3CT.
template<typename R>
struct Constellation_symbols : public Constellation<R>
{
    Constellation_symbols(const std::vector<typename Constellation<R>::S>& symbols, const std::string& name)
      : Constellation<R>(symbols, name)
    {
    }
};

template<typename R>
static void
wrap_constellations_internal(py::handle scope)
{
    using C = Constellation<R>;
    using S = std::complex<R>;
    py::class_<C>(scope,
                  class_name<R>("Constellation").c_str(),
                  R"pbdoc(Base class of the constellations of the generic modems (PSK, PAM, QAM, user).

The symbol ``i`` is the image of the bits of ``i``, the first bit being the least significant one.

>>> cstl = af.tools.Constellation_QAM(4)          # 16-QAM
>>> cstl.symbols                                   # numpy.ndarray[complex64]
>>> mdm = af.mdm.modem(N, cstl)                    # generic modem (keeps the constellation alive)
>>> cstl = af.tools.Constellation(np.exp(2j * np.pi * np.arange(8) / 8))   # any symbols
)pbdoc")
      .def(
        py::init(
          [](const std::vector<S>& symbols, bool normalize, const std::string& name)
          {
              std::vector<S> s = symbols;
              if (normalize && !s.empty())
              {
                  R es = 0;
                  for (auto& x : s)
                      es += std::norm(x);
                  const auto k = std::sqrt(es / (R)s.size());
                  for (auto& x : s)
                      x /= k;
              }
              return static_cast<C*>(new Constellation_symbols<R>(s, name));
          }),
        "symbols"_a,
        "normalize"_a = true,
        "name"_a = "User<C>",
        R"pbdoc(Constellation of the given symbols (2^bps of them; the symbol ``i`` is the image of the bits of ``i``, LSB first).

Args:
    symbols (array-like of complex): the symbols.
    normalize (bool): scale them to a unit mean energy (as the constellation files of AFF3CT).
    name (str): name of the constellation.
)pbdoc")
      .def_property_readonly("name", &C::get_name, "str: name (e.g. 'QAM').")
      .def_property_readonly("bps", &C::get_n_bits_per_symbol, "int: number of bits per symbol.")
      .def_property_readonly("n_symbols", &C::get_n_symbols, "int: number of symbols (2^bps).")
      .def("is_complex", &C::is_complex, "Return True if a symbol has a non-zero imaginary part.")
      .def_property_readonly(
        "symbols",
        [](const C& c)
        {
            py::array_t<S> a((py::ssize_t)c.size());
            auto p = a.mutable_data();
            for (size_t i = 0; i < c.size(); i++)
                p[i] = c.get_symbol(i);
            return a;
        },
        "numpy.ndarray[complex]: the symbols (a copy).")
      .def(
        "__getitem__",
        [](const C& c, py::ssize_t i)
        {
            if (i < 0) i += (py::ssize_t)c.size();
            if (i < 0 || i >= (py::ssize_t)c.size()) throw py::index_error("symbol index out of range");
            return c.get_symbol((size_t)i);
        },
        "i"_a)
      .def("__len__", &C::size)
      .def("__repr__",
           [](const C& c) {
               return c.get_name() + " constellation (" + std::to_string(c.get_n_bits_per_symbol()) +
                      " bits per symbol)";
           });

    py::class_<Constellation_PAM<R>, C>(
      scope, class_name<R>("Constellation_PAM").c_str(), "Pulse amplitude modulation (Gray mapping, unit energy).")
      .def(py::init<unsigned>(), "bps"_a);
    py::class_<Constellation_PSK<R>, C>(
      scope, class_name<R>("Constellation_PSK").c_str(), "Phase shift keying (Gray mapping, unit energy).")
      .def(py::init<unsigned>(), "bps"_a);
    py::class_<Constellation_QAM<R>, C>(
      scope, class_name<R>("Constellation_QAM").c_str(), "Square quadrature amplitude modulation (bps even).")
      .def(py::init<unsigned>(), "bps"_a);
    py::class_<Constellation_user<R>, C>(
      scope,
      class_name<R>("Constellation_user").c_str(),
      "Constellation read from a file (one symbol per line: real part, and imaginary part if complex).")
      .def(py::init<const std::string&>(), "path"_a);
}
} // namespace wrapper
} // namespace pyaf

void
pyaf::wrapper::wrap_constellations(py::handle scope)
{
    for_each_combo<gen::Tools_Constellation>(
      [&](auto c) { wrap_constellations_internal<typename decltype(c)::template at<0>>(scope); });
}
