#include <fstream>

#include <pybind11/stl/filesystem.h>

#include "Tools/Code/LDPC/AList/AList.hpp"
#include "Tools/Code/LDPC/Matrix_handler/LDPC_matrix_handler.hpp"
#include "Tools/Code/LDPC/QC/QC.hpp"

#include "internal/Wrapper/Tools/Code/LDPC.hpp"

using namespace aff3ct::tools;
using path = std::filesystem::path;

namespace
{
std::ifstream
open_in(const path& p)
{
    std::ifstream f(p);
    if (!f.is_open()) throw py::value_error("cannot open '" + p.string() + "'.");
    return f;
}

std::ofstream
open_out(const path& p)
{
    std::ofstream f(p);
    if (!f.is_open()) throw py::value_error("cannot write '" + p.string() + "'.");
    return f;
}
} // namespace

void
pyaf::wrapper::wrap_ldpc_tools(py::handle scope)
{
    py::class_<AList>(scope, "AList", R"pbdoc(Reader / writer of the AList format (LDPC matrices), static methods.

>>> H = af.tools.AList.read("H.alist")
>>> af.tools.AList.write(H, "copy.alist")
)pbdoc")
      .def_static(
        "read",
        [](const path& p)
        {
            auto f = open_in(p);
            return AList::read(f);
        },
        "path"_a,
        "Read a matrix (aff3ct.tools.Sparse_matrix).")
      .def_static(
        "write",
        [](const Sparse_matrix& H, const path& p, bool zero_padding)
        {
            auto f = open_out(p);
            AList::write(H, f, zero_padding);
        },
        "matrix"_a,
        "path"_a,
        "zero_padding"_a = false,
        "Write a matrix.")
      .def_static(
        "read_matrix_size",
        [](const path& p)
        {
            auto f = open_in(p);
            int H = 0, N = 0;
            AList::read_matrix_size(f, H, N);
            return py::make_tuple(H, N);
        },
        "path"_a,
        "(number of rows, number of columns) of the matrix of a file.")
      .def_static(
        "read_info_bits_pos",
        [](const path& p, std::optional<int> K, std::optional<int> N)
        {
            auto f = open_in(p);
            AList::read(f); // the positions follow the matrix
            auto pos = (K && N) ? AList::read_info_bits_pos(f, *K, *N) : AList::read_info_bits_pos(f);
            return to_numpy(std::vector<uint32_t>(pos.begin(), pos.end()));
        },
        "path"_a,
        "K"_a = py::none(),
        "N"_a = py::none(),
        "Positions of the information bits written after the matrix (checked against K and N when given).");

    py::class_<QC>(scope, "QC", "Reader / writer of the quasi-cyclic format (LDPC matrices), static methods.")
      .def_static(
        "read",
        [](const path& p)
        {
            auto f = open_in(p);
            return QC::read(f);
        },
        "path"_a,
        "Read a matrix (aff3ct.tools.Sparse_matrix).")
      .def_static(
        "read_pct_pattern",
        [](const path& p, int N_red)
        {
            auto f = open_in(p);
            return QC::read_pct_pattern(f, N_red);
        },
        "path"_a,
        "N_red"_a = -1,
        "Puncturing pattern of the file (numpy.ndarray[bool]).")
      .def_static(
        "write",
        [](const Sparse_matrix& H, const path& p)
        {
            auto f = open_out(p);
            QC::write(H, f);
        },
        "matrix"_a,
        "path"_a,
        "Write a matrix.");

    using L = LDPC_matrix_handler;
    py::class_<L>(scope, "LDPC_matrix_handler", "LDPC matrix utilities (format detection, H -> G), static methods.")
      .def_static(
        "read",
        [](const path& p)
        {
            L::Positions_vector info_bits_pos;
            std::vector<bool> pct_pattern;
            auto H = L::read(p.string(), &info_bits_pos, &pct_pattern);
            return py::make_tuple(H, to_numpy(info_bits_pos), pct_pattern);
        },
        "path"_a,
        R"pbdoc(Read an AList or QC file (format detected).

Returns:
    out (tuple): ``(H, info_bits_pos, pct_pattern)``: the matrix, the positions of the information bits (empty if the
    file has none) and the puncturing pattern (QC files, empty otherwise).
)pbdoc")
      .def_static(
        "transform_H_to_G",
        [](const Sparse_matrix& H_any, const std::string& method)
        {
            L::Positions_vector info_bits_pos;
            Sparse_matrix G;
            const auto H = H_any.turn(Matrix::Way::HORIZONTAL); // M x N expected, whatever the file orientation
            if (method == "IDENTITY")
                G = L::transform_H_to_G_identity(H, info_bits_pos);
            else if (method == "LU_DEC")
                G = L::transform_H_to_G_decomp_LU(H, info_bits_pos);
            else
                throw py::value_error("method must be 'IDENTITY' or 'LU_DEC' (got '" + method + "').");
            return py::make_tuple(G, to_numpy(info_bits_pos));
        },
        "H"_a,
        "method"_a = "IDENTITY",
        R"pbdoc(Generator matrix of a parity-check matrix (methods of the ``--enc-g-method`` option), H in any orientation.

The encoder of type ``"LDPC_H"`` does it itself: ``af.enc.ldpc(K, N, af.tools.Sparse_matrix(), H, type="LDPC_H")``,
its ``info_bits_pos`` being then given to the decoder.

Returns:
    out (tuple): ``(G, info_bits_pos)``.
)pbdoc")
      .def_static("check_GH",
                  py::overload_cast<const Sparse_matrix&, const Sparse_matrix&>(&L::check_GH),
                  "H"_a,
                  "G"_a,
                  "Return True if G x H^T = 0.")
      .def_static(
        "check_info_pos",
        [](const std::vector<uint32_t>& pos, int K, int N) { return L::check_info_pos(pos, K, N, false); },
        "info_bits_pos"_a,
        "K"_a,
        "N"_a,
        "Return True if info_bits_pos are K distinct positions lower than N.");
}
