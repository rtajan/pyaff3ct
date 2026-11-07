#include "Tools/Code/Polar/Frozenbits_generator/Frozenbits_generator.hpp"
#include "Tools/Code/Polar/Frozenbits_generator/Frozenbits_generator_BEC.hpp"
#include "Tools/Code/Polar/Frozenbits_generator/Frozenbits_generator_GA_Arikan.hpp"
#include "Tools/Code/Polar/Frozenbits_generator/Frozenbits_generator_file.hpp"
#include "Tools/Interface/Interface_get_set_noise.hpp"

#include "internal/Wrapper/Tools/Code/Frozenbits_generator.hpp"

using namespace aff3ct::tools;

void
pyaf::wrapper::wrap_frozenbits_generator(py::handle scope)
{
    using G = Frozenbits_generator;
    py::class_<G, Interface_get_set_noise>(scope,
                                           "Frozenbits_generator",
                                           R"pbdoc(Base class of the frozen bits generators (polar codes).

The generator sorts the N bit channels by reliability for a given noise, then freezes the N - K worst ones.

>>> gen = af.tools.Frozenbits_generator_GA_Arikan(K=64, N=128)
>>> frozen_bits = gen.generate(af.tools.sigma_from_ebn0(2.0, code_rate=64 / 128))
)pbdoc")
      .def_property_readonly("K", &G::get_K, "int: number of information bits.")
      .def_property_readonly("N", &G::get_N, "int: codeword size.")
      .def(
        "generate",
        [](G& g, const Noise<>* noise)
        {
            if (noise != nullptr) g.set_noise(*noise);
            std::vector<bool> fb(g.get_N());
            g.generate(fb);
            return fb;
        },
        "noise"_a = nullptr,
        py::keep_alive<1, 2>(),
        R"pbdoc(Compute the frozen bits.

Args:
    noise (aff3ct.tools.Noise_float32, optional): noise used to sort the channels (set_noise), kept by the
        generator; the current one when omitted.

Returns:
    out (numpy.ndarray[bool]): N values, True for a frozen bit.
)pbdoc")
      .def_property_readonly(
        "best_channels",
        [](const G& g) { return to_numpy(g.get_best_channels()); },
        "numpy.ndarray[uint32]: bit channels sorted from the most to the least reliable (after generate).")
      .def("dump_best_channels", &G::dump_best_channels, "path"_a, "Write the sorted channels into a file.");

    py::class_<Frozenbits_generator_GA_Arikan, G>(
      scope,
      "Frozenbits_generator_GA_Arikan",
      "Gaussian approximation (Arikan kernel): the reliabilities depend on the noise (Sigma) given to generate().")
      .def(py::init<int, int, const std::string&, bool>(),
           "K"_a,
           "N"_a,
           "dump_channels_path"_a = "",
           "dump_channels_single_thread"_a = true);
    py::class_<Frozenbits_generator_BEC, G>(
      scope,
      "Frozenbits_generator_BEC",
      "Bhattacharyya parameters on the binary erasure channel (noise: Event_probability).")
      .def(py::init<int, int, const std::string&, bool>(),
           "K"_a,
           "N"_a,
           "dump_channels_path"_a = "",
           "dump_channels_single_thread"_a = true);
    py::class_<Frozenbits_generator_file, G>(
      scope, "Frozenbits_generator_file", "Sorted channels read from a file (independent of the noise).")
      .def(py::init<int, int, const std::string&>(), "K"_a, "N"_a, "filename"_a);
}
