#include <sstream>

#include <cli.hpp>

#include "Tools/Factory/Header.hpp"

#include "internal/Wrapper/Factory/Factory.hpp"

using aff3ct::factory::Factory;

namespace
{
//! Parses AFF3CT command line arguments into a factory (only the given arguments are changed).
void
factory_from_cli(Factory& f, const std::vector<std::string>& cmd, bool strict)
{
    cli::Argument_map_info args;
    f.get_description(args);
    // the factory already holds a value for every parameter: none of them is required here
    for (auto& a : args)
        if (a.second->rank == cli::arg_rank::REQ) a.second->rank = cli::arg_rank::OPT;

    std::vector<const char*> argv{ "aff3ct" };
    for (auto& s : cmd)
        argv.push_back(s.c_str());

    std::ostringstream help;
    cli::Argument_handler ah((int)argv.size(), argv.data(), help);
    std::vector<std::string> warnings, errors;
    auto values = ah.parse_arguments(args, warnings, errors);

    // an unknown argument is a typo or an argument of another factory: rejected, unless not strict (a whole AFF3CT
    // command line given to each factory)
    std::vector<std::string> kept;
    for (auto& w : warnings)
        if (w.rfind("Unknown argument", 0) == 0)
        {
            if (strict) errors.push_back(w);
        }
        else
            kept.push_back(w);
    warnings = kept;
    if (!errors.empty())
    {
        std::string msg = "invalid AFF3CT arguments for the factory '" + f.get_name() + "':";
        for (auto& e : errors)
            msg += "\n  - " + e;
        throw py::value_error(msg);
    }
    for (auto& w : warnings)
        if (PyErr_WarnEx(PyExc_UserWarning, w.c_str(), 1) != 0) throw py::error_already_set();

    f.store(values);
}

//! Runs the AFF3CT `store()` with no argument: only the derived values are computed (CRC size from the polynomial,
//! code rate from K and N_cw...), exactly as after a command-line parsing.
void
factory_complete(Factory& f)
{
    cli::Argument_map_value none;
    f.store(none);
}

py::dict
factory_headers(const Factory& f, const bool full)
{
    std::map<std::string, aff3ct::tools::header_list> headers;
    f.get_headers(headers, full);
    py::dict res;
    for (auto& h : headers)
    {
        py::dict section;
        for (auto& kv : h.second)
            section[py::str(kv.first)] = kv.second;
        res[py::str(h.first)] = section;
    }
    return res;
}

void
factory_print_help(const Factory& f, const bool advanced)
{
    cli::Argument_map_info args;
    f.get_description(args);
    std::vector<const char*> argv{ "aff3ct" };
    std::ostringstream help;
    cli::Argument_handler ah((int)argv.size(), argv.data(), help);
    ah.print_help(args, advanced);
    py::print(help.str(), "end"_a = "");
}
} // namespace

void
pyaf::wrapper::wrap_factory(py::handle scope)
{
    py::class_<Factory, spu::tools::Interface_clone> cls(scope,
                                                         "Factory",
                                                         R"pbdoc(Base class of the AFF3CT factories.

Factories are hidden behind the module-level functions (``aff3ct.crc.polynomial(...)``); use them directly only
for the command-line parity (``from_cli``) or to inspect the parameters (``headers``, ``print_help``).
)pbdoc");
    cls.attr("_parameters") = py::tuple();
    cls.def_property_readonly("name", &Factory::get_name, "str: name of the factory.")
      .def_property_readonly("short_name", &Factory::get_short_name, "str: short name of the factory.")
      .def_property_readonly("prefix", &Factory::get_prefix, "str: prefix of the command line arguments (e.g. 'crc').")
      .def("from_cli",
           &factory_from_cli,
           "args"_a,
           "strict"_a = true,
           R"pbdoc(Set parameters from AFF3CT command-line arguments (only the given ones change).

Args:
    args (list[str]): arguments, e.g. ``["--crc-poly", "32-GZIP", "--crc-implem", "STD"]``.
    strict (bool): reject the arguments that are not of this factory (False: ignore them, to give the same whole
        AFF3CT command line to several factories).

Raises:
    ValueError: if an argument is unknown (strict) or has an invalid value.
)pbdoc")
      .def("headers",
           &factory_headers,
           "full"_a = true,
           "Return the parameters as printed by AFF3CT: {section: {parameter: value}}.")
      .def("print_help", &factory_print_help, "advanced"_a = true, "Print the command-line help of the factory.")
      .def("clone", &Factory::clone, py::return_value_policy::take_ownership, "Return a copy of the factory.")
      .def("_complete",
           &factory_complete,
           "Compute the derived parameters as AFF3CT does after parsing the command line (internal, used by build).");
}
