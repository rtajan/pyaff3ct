#include "internal/Wrapper/Testing/Testing.hpp"

void
pyaf::wrapper::wrap_testing(py::module_ scope)
{
    scope.def(
      "bool_vector_roundtrip",
      [](const std::vector<bool>& v) { return v; },
      "v"_a,
      "Convert `v` to std::vector<bool> and back (caster test).");
    scope.def(
      "bool_vector_size",
      [](const std::vector<bool>& v) { return v.size(); },
      "v"_a,
      "Size of `v` once converted to std::vector<bool> (caster test).");
}
