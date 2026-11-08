#include "Tools/Code/Polar/Frozenbits_generator/Frozenbits_generator.hpp"
#include "Tools/Code/Polar/Frozenbits_generator/Frozenbits_generator_5G.hpp"
#include "Tools/Code/Polar/Frozenbits_generator/Frozenbits_generator_BEC.hpp"
#include "Tools/Code/Polar/Frozenbits_generator/Frozenbits_generator_GA.hpp"
#include "Tools/Code/Polar/Frozenbits_generator/Frozenbits_generator_GA_Arikan.hpp"
#include "Tools/Code/Polar/Frozenbits_generator/Frozenbits_generator_RM.hpp"
#include "Tools/Code/Polar/Frozenbits_generator/Frozenbits_generator_TV.hpp"
#include "Tools/Code/Polar/Frozenbits_generator/Frozenbits_generator_file.hpp"
#include "Tools/Code/Polar/Polar_code.hpp"
#include "Tools/Code/Polar/Pretransform_generator/Pretransform_generator.hpp"
#include "Tools/Code/Polar/Pretransform_generator/Pretransform_generator_file.hpp"
#include "Tools/Interface/Interface_get_set_noise.hpp"

#include "internal/Wrapper/Tools/Code/Frozenbits_generator.hpp"

using namespace aff3ct::tools;

void
pyaf::wrapper::wrap_frozenbits_generator(py::handle scope)
{
    py::class_<Polar_code>(scope,
                           "Polar_code",
                           R"pbdoc(Kernel(s) of a polar code: Arikan kernel by default, multi-kernel codes (polar MK).

>>> code = af.tools.Polar_code(16, [[1, 0], [1, 1]])            # N = 16, Arikan kernel
>>> code = af.tools.Polar_code([[[1, 0], [1, 1]], [[1, 1, 1], [1, 0, 1], [0, 1, 1]]], [0, 0, 1])   # 2 x 2 x 3
>>> code = af.tools.Polar_code("conf/cde/polar_mk/N24_K12.pc")  # from a file
)pbdoc")
      .def(py::init<const std::string&>(), "path"_a, "Code read from a file.")
      .def(py::init<int, const std::vector<std::vector<bool>>&>(),
           "N"_a,
           "kernel"_a,
           "Code of size N built with a single kernel (N must be a power of its size).")
      .def(py::init<const std::vector<std::vector<std::vector<bool>>>&, const std::vector<uint32_t>&>(),
           "kernels"_a,
           "stages"_a,
           "Multi-kernel code: kernels[stages[i]] is the kernel of the stage i.")
      .def_property_readonly("N", &Polar_code::get_codeword_size, "int: codeword size.")
      .def_property_readonly("kernels", &Polar_code::get_kernel_matrices, "list: kernel matrices.")
      .def_property_readonly("stages", &Polar_code::get_stages, "list[int]: kernel of each stage.")
      .def_property_readonly(
        "biggest_kernel_size", &Polar_code::get_biggest_kernel_size, "int: size of the biggest kernel.")
      .def("can_be_systematic", &Polar_code::can_be_systematic)
      .def("is_mono_kernel", [](const Polar_code& c) { return c.is_mono_kernel() != 0; });

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
    py::class_<Frozenbits_generator_GA, G>(
      scope,
      "Frozenbits_generator_GA",
      "Gaussian approximation for any polar code (multi-kernel included): density evolution on the given code.")
      .def(py::init<int, int, const Polar_code&, const std::string&, bool>(),
           "K"_a,
           "N"_a,
           "code"_a,
           "dump_channels_path"_a = "",
           "dump_channels_single_thread"_a = true,
           py::keep_alive<1, 4>());
    py::class_<Frozenbits_generator_RM, G>(
      scope, "Frozenbits_generator_RM", "Reed-Muller construction (row weights; independent of the noise).")
      .def(py::init<int, int, const std::string&, bool>(),
           "K"_a,
           "N"_a,
           "dump_channels_path"_a = "",
           "dump_channels_single_thread"_a = true);
    py::class_<Frozenbits_generator_5G, Frozenbits_generator_file>(
      scope, "Frozenbits_generator_5G", "Reliability sequence of the 5G standard (3GPP TS 38.212, N <= 1024).")
      .def(py::init<int, int>(), "K"_a, "N"_a);
    py::class_<Frozenbits_generator_TV, Frozenbits_generator_file>(
      scope,
      "Frozenbits_generator_TV",
      "Tal & Vardy construction (precomputed files of the AWGN codes, external binary for the others).")
      .def(py::init<int, int, const std::string&, const std::string&>(),
           "K"_a,
           "N"_a,
           "awgn_codes_dir"_a,
           "bin_pb_path"_a);

    using P = Pretransform_generator;
    py::class_<P, Interface_get_set_noise>(
      scope, "Pretransform_generator", "Base class of the pre-transformation generators (pre-transformed polar codes).")
      .def_property_readonly("K", &P::get_K)
      .def_property_readonly("N", &P::get_N)
      .def(
        "generate",
        [](P& g, const Noise<>* noise)
        {
            if (noise != nullptr) g.set_noise(*noise);
            std::vector<bool> fb(g.get_N());
            g.generate(fb);
            return fb;
        },
        "noise"_a = nullptr,
        py::keep_alive<1, 2>(),
        "Compute the frozen bits (numpy.ndarray[bool]), and the pre-transformation (pre_transform).")
      .def_property_readonly(
        "best_channels", [](const P& g) { return to_numpy(g.get_best_channels()); }, "numpy.ndarray[uint32]")
      .def_property_readonly(
        "pre_transform", &P::get_pre_transform, "dict[int, list[int]]: pre-transformation (after generate).");
    py::class_<Pretransform_generator_file, P>(
      scope, "Pretransform_generator_file", "Pre-transformation read from a file.")
      .def(py::init<int, int, const std::string&>(), "K"_a, "N"_a, "filename"_a);
}
