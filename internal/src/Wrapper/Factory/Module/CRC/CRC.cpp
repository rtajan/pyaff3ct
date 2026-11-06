#include "Factory/Module/CRC/CRC.hpp"

#include "internal/Wrapper/Factory/Module/CRC/CRC.hpp"

void
pyaf::wrapper::wrap_factory_crc(py::handle scope)
{
    using F = aff3ct::factory::CRC;
    py::class_<F, aff3ct::factory::Factory> cls(scope, "CRC", "Factory of the CRCs (``--crc-*`` arguments).");
    cls.def(py::init<const std::string&>(), "prefix"_a = aff3ct::factory::CRC_prefix);
    def_param(cls, "K", &F::K, "int: number of information bits (without the CRC bits).");
    def_param(cls, "type", &F::type, "str: CRC polynomial, by name ('32-GZIP', '8-DVB-S2'...) or value; 'NO' for none.");
    def_param(cls, "implem", &F::implem, "str: implementation, 'STD', 'FAST' or 'INTER'.");
    def_param(cls, "size", &F::size, "int: CRC size in bits (0 = deduced from the polynomial).");
    def_builders<gen::Factory_CRC__build>(cls,
                                          "build",
                                          [](auto c)
                                          {
                                              using B = typename decltype(c)::template at<0>;
                                              return [](const F& f) { return f.template build<B>(); };
                                          });
}
