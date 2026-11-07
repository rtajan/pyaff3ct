#include "Tools/Math/Galois.hpp"
#include "Tools/Code/BCH/BCH_polynomial_generator.hpp"
#include "Tools/Code/RS/RS_polynomial_generator.hpp"

#include "internal/Wrapper/Tools/Code/Galois.hpp"

using namespace aff3ct::tools;

namespace pyaf
{
namespace wrapper
{
template<typename I>
static void
wrap_galois_internal(py::handle scope)
{
    using G = Galois<I>;
    py::class_<G>(scope, class_name<I>("Galois").c_str(), "Galois field GF(2^m) of a code of length N = 2^m - 1.")
      .def(py::init<int, std::vector<I>>(),
           "N"_a,
           "p"_a = std::vector<I>(),
           "Field of the codes of length N; p: primitive polynomial (default: the one of AFF3CT for m).")
      .def_property_readonly("N", &G::get_N, "int: code length (2^m - 1).")
      .def_property_readonly("m", &G::get_m, "int: order of the field.")
      .def_property_readonly(
        "alpha_to", [](const G& g) { return to_numpy(g.get_alpha_to()); }, "numpy.ndarray: powers of alpha.")
      .def_property_readonly(
        "index_of", [](const G& g) { return to_numpy(g.get_index_of()); }, "numpy.ndarray: logarithms (index of).")
      .def_property_readonly(
        "p", [](const G& g) { return to_numpy(g.get_p()); }, "numpy.ndarray: primitive polynomial.");

    using P = BCH_polynomial_generator<I>;
    py::class_<P, G>(scope,
                     class_name<I>("BCH_polynomial_generator").c_str(),
                     R"pbdoc(Generator polynomial of a BCH code (given to the BCH encoder and decoder).

>>> GF = af.tools.BCH_polynomial_generator(N=15, t=2)
>>> enc = af.enc.bch(GF.N - GF.n_rdncy, GF.N, GF)
)pbdoc")
      .def(py::init<int, int, std::vector<I>>(),
           "N"_a,
           "t"_a,
           "p"_a = std::vector<I>(),
           "Code of length N correcting t errors; p: primitive polynomial (default: the one of AFF3CT).")
      .def_property_readonly("t", &P::get_t, "int: correction power.")
      .def_property_readonly("d", &P::get_d, "int: minimum distance.")
      .def_property_readonly("n_rdncy", &P::get_n_rdncy, "int: number of redundancy bits (N - K).")
      .def_property_readonly(
        "g", [](const P& p) { return to_numpy(p.get_g()); }, "numpy.ndarray: generator polynomial.");
}
} // namespace wrapper
} // namespace pyaf

void
pyaf::wrapper::wrap_galois(py::handle scope)
{
    for_each_combo<gen::Tools_BCH_polynomial_generator>(
      [&](auto c) { wrap_galois_internal<typename decltype(c)::template at<0>>(scope); });

    using P = RS_polynomial_generator;
    py::class_<P, Galois<int>>(scope,
                               "RS_polynomial_generator",
                               R"pbdoc(Generator polynomial of a Reed-Solomon code (symbols of m bits).

>>> GF = af.tools.RS_polynomial_generator(N=15, t=2)
>>> enc = af.enc.rs(GF.N - GF.n_rdncy, GF.N, GF)   # sizes in symbols (enc.K, enc.N in bits)
)pbdoc")
      .def(py::init<int, int>(), "N"_a, "t"_a, "Code of N symbols correcting t symbol errors.")
      .def_property_readonly("t", &P::get_t, "int: correction power (symbols).")
      .def_property_readonly("d", &P::get_d, "int: minimum distance.")
      .def_property_readonly("n_rdncy", &P::get_n_rdncy, "int: number of redundancy symbols.")
      .def_property_readonly(
        "g", [](const P& p) { return to_numpy(p.get_g()); }, "numpy.ndarray: generator polynomial.")
      .def_property_readonly(
        "mt", [](const P& p) { return to_numpy(p.get_mt()); }, "numpy.ndarray: multiplication table.");
}
