#include <sstream>

#include "Tools/Algo/Matrix/Matrix.hpp"
#include "Tools/Algo/Matrix/Sparse_matrix/Sparse_matrix.hpp"

#include "internal/Wrapper/Tools/Algo/Sparse_matrix.hpp"

using namespace aff3ct::tools;

namespace
{
Sparse_matrix
from_dense(const py::array& a)
{
    // any numeric / bool 2D array: non-zero = connection
    auto b = py::array::ensure(py::module_::import("numpy").attr("not_equal")(a, 0), py::array::c_style);
    if (b.ndim() != 2)
        throw py::value_error("a Sparse_matrix is built from a 2D array (got " + std::to_string(b.ndim()) + "D).");
    auto m = b.cast<py::array_t<bool, py::array::c_style | py::array::forcecast>>().unchecked<2>();
    Sparse_matrix s((size_t)m.shape(0), (size_t)m.shape(1));
    for (py::ssize_t r = 0; r < m.shape(0); r++)
        for (py::ssize_t c = 0; c < m.shape(1); c++)
            if (m(r, c)) s.add_connection((size_t)r, (size_t)c);
    return s;
}

py::array_t<uint8_t>
to_dense(const Sparse_matrix& s)
{
    py::array_t<uint8_t> a({ (py::ssize_t)s.get_n_rows(), (py::ssize_t)s.get_n_cols() });
    auto m = a.mutable_unchecked<2>();
    std::fill(a.mutable_data(), a.mutable_data() + a.size(), 0);
    for (size_t r = 0; r < s.get_n_rows(); r++)
        for (auto c : s.get_cols_from_row(r))
            m(r, c) = 1;
    return a;
}

bool
same(const Sparse_matrix& a, const Sparse_matrix& b)
{
    if (a.get_n_rows() != b.get_n_rows() || a.get_n_cols() != b.get_n_cols()) return false;
    if (a.get_n_connections() != b.get_n_connections()) return false;
    for (size_t r = 0; r < a.get_n_rows(); r++)
        for (auto c : a.get_cols_from_row(r))
            if (!b.at(r, c)) return false;
    return true;
}

py::tuple
nonzero(const Sparse_matrix& s)
{
    py::array_t<uint32_t> rows((py::ssize_t)s.get_n_connections()), cols((py::ssize_t)s.get_n_connections());
    auto pr = rows.mutable_data();
    auto pc = cols.mutable_data();
    size_t i = 0;
    for (size_t r = 0; r < s.get_n_rows(); r++)
        for (auto c : s.get_cols_from_row(r))
        {
            pr[i] = (uint32_t)r;
            pc[i] = c;
            i++;
        }
    return py::make_tuple(rows, cols);
}
} // namespace

void
pyaf::wrapper::wrap_sparse_matrix(py::handle scope)
{
    py::class_<Matrix> mat(scope, "Matrix", "Base class of the AFF3CT binary matrices (Sparse_matrix...).");
    py::enum_<Matrix::Way>(mat, "Way", "Orientation of a matrix.")
      .value("HORIZONTAL", Matrix::Way::HORIZONTAL, "More columns than rows.")
      .value("VERTICAL", Matrix::Way::VERTICAL, "More rows than columns.");
    py::enum_<Matrix::Sort>(mat, "Sort", "Order of a sort.")
      .value("ASCENDING", Matrix::Sort::ASCENDING)
      .value("DESCENDING", Matrix::Sort::DESCENDING);
    py::enum_<Matrix::Origin>(mat, "Origin", "Corner kept by a resize.")
      .value("TOP_LEFT", Matrix::Origin::TOP_LEFT)
      .value("TOP_RIGHT", Matrix::Origin::TOP_RIGHT)
      .value("BOTTOM_LEFT", Matrix::Origin::BOTTOM_LEFT)
      .value("BOTTOM_RIGHT", Matrix::Origin::BOTTOM_RIGHT);
    mat.def_property_readonly("n_rows", &Matrix::get_n_rows, "int: number of rows.")
      .def_property_readonly("n_cols", &Matrix::get_n_cols, "int: number of columns.")
      .def_property_readonly(
        "shape", [](const Matrix& m) { return py::make_tuple(m.get_n_rows(), m.get_n_cols()); }, "tuple[int, int]")
      .def_property_readonly("n_connections", &Matrix::get_n_connections, "int: number of ones.")
      .def_property_readonly("rows_max_degree", &Matrix::get_rows_max_degree, "int: largest number of ones of a row.")
      .def_property_readonly(
        "cols_max_degree", &Matrix::get_cols_max_degree, "int: largest number of ones of a column.")
      .def_property_readonly("way", &Matrix::get_way, "Matrix.Way: orientation.")
      .def_property_readonly("density", &Matrix::compute_density, "float: proportion of ones.")
      .def("at", &Matrix::at, "row"_a, "col"_a, "Return True if (row, col) is a one.");

    py::class_<Sparse_matrix, Matrix>(scope,
                                      "Sparse_matrix",
                                      R"pbdoc(Binary sparse matrix (LDPC parity-check and generator matrices).

>>> H = af.tools.Sparse_matrix(np.array([[1, 1, 0, 1], [0, 1, 1, 1]]))   # from any 2D array
>>> H.to_dense()                    # numpy.ndarray[uint8]
>>> H.to_scipy()                    # scipy.sparse.csr_matrix (scipy needed)
>>> af.tools.Sparse_matrix.from_scipy(H.to_scipy())
>>> H[0, 1], H.row_to_cols, H.T
)pbdoc")
      .def(py::init<size_t, size_t>(), "n_rows"_a = 0, "n_cols"_a = 1, "Empty matrix (no connection).")
      .def(py::init(&from_dense), "array"_a, "Matrix whose ones are the non-zero values of a 2D array.")
      .def_static(
        "from_scipy",
        [](const py::object& m)
        {
            auto coo = m.attr("tocoo")();
            auto shape = coo.attr("shape").cast<std::pair<size_t, size_t>>();
            auto rows = coo.attr("row").cast<std::vector<int64_t>>();
            auto cols = coo.attr("col").cast<std::vector<int64_t>>();
            auto data = py::module_::import("numpy").attr("asarray")(coo.attr("data")).cast<py::array>();
            auto nz = py::module_::import("numpy").attr("not_equal")(data, 0).cast<std::vector<bool>>();
            Sparse_matrix s(shape.first, shape.second);
            for (size_t i = 0; i < rows.size(); i++)
                if (nz[i] && !s.at(rows[i], cols[i])) s.add_connection(rows[i], cols[i]);
            return s;
        },
        "matrix"_a,
        "Matrix from a scipy.sparse matrix (any format with tocoo(); non-zero values = ones).")
      .def("to_dense", &to_dense, "Dense copy (numpy.ndarray[uint8] of 0 / 1).")
      .def(
        "__array__",
        [](const Sparse_matrix& s, py::object dtype, py::object /*copy*/)
        {
            py::object a = to_dense(s);
            return dtype.is_none() ? a : a.attr("astype")(dtype);
        },
        "dtype"_a = py::none(),
        "copy"_a = py::none())
      .def("nonzero", &nonzero, "(rows, cols) of the ones (numpy.ndarray[uint32]), row by row.")
      .def(
        "to_scipy",
        [](const Sparse_matrix& s)
        {
            auto rc = nonzero(s);
            auto np = py::module_::import("numpy");
            auto ones = np.attr("ones")(s.get_n_connections(), "dtype"_a = np.attr("uint8"));
            return py::module_::import("scipy.sparse")
              .attr("csr_matrix")(py::make_tuple(ones, rc), "shape"_a = py::make_tuple(s.get_n_rows(), s.get_n_cols()));
        },
        "Copy as a scipy.sparse.csr_matrix of uint8 (needs scipy).")
      .def(
        "__getitem__",
        [](const Sparse_matrix& s, std::pair<size_t, size_t> rc) { return s.at(rc.first, rc.second); },
        "(row, col) -> True if one.")
      .def("add_connection", &Sparse_matrix::add_connection, "row"_a, "col"_a, "Set (row, col) to one.")
      .def("rm_connection", &Sparse_matrix::rm_connection, "row"_a, "col"_a, "Set (row, col) to zero.")
      .def(
        "cols_from_row",
        [](const Sparse_matrix& s, size_t r) { return to_numpy(s.get_cols_from_row(r)); },
        "row"_a,
        "Columns of the ones of a row (numpy.ndarray[uint32]).")
      .def(
        "rows_from_col",
        [](const Sparse_matrix& s, size_t c) { return to_numpy(s.get_rows_from_col(c)); },
        "col"_a,
        "Rows of the ones of a column (numpy.ndarray[uint32]).")
      .def_property_readonly("row_to_cols", &Sparse_matrix::get_row_to_cols, "list[list[int]]: columns of each row.")
      .def_property_readonly("col_to_rows", &Sparse_matrix::get_col_to_rows, "list[list[int]]: rows of each column.")
      .def("transpose", &Sparse_matrix::transpose, "Transposed copy.")
      .def_property_readonly("T", &Sparse_matrix::transpose, "Transposed copy.")
      .def("turn", &Sparse_matrix::turn, "way"_a, "Copy with the given orientation (transposed if needed).")
      .def("resize",
           &Sparse_matrix::resize,
           "n_rows"_a,
           "n_cols"_a,
           py::arg_v("origin", Matrix::Origin::TOP_LEFT, "aff3ct.tools.Matrix.Origin.TOP_LEFT"),
           "Resized copy, the given corner being kept.")
      .def("sort_cols_per_density", &Sparse_matrix::sort_cols_per_density, "order"_a, "Sort the columns by degree.")
      .def_static("identity", &Sparse_matrix::identity, "n_rows"_a, "n_cols"_a, "Identity matrix.")
      .def_static("zero", &Sparse_matrix::zero, "n_rows"_a, "n_cols"_a, "Matrix without connection.")
      .def("__eq__", &same, "other"_a, "Same shape and same ones.")
      .def("__str__",
           [](const Sparse_matrix& s)
           {
               std::stringstream ss;
               s.print(false, ss);
               return ss.str();
           })
      .def("__repr__",
           [](const Sparse_matrix& s)
           {
               return "Sparse_matrix(" + std::to_string(s.get_n_rows()) + "x" + std::to_string(s.get_n_cols()) + ", " +
                      std::to_string(s.get_n_connections()) + " ones)";
           });
}
