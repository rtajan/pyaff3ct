#include <vector>

#include "internal/Common/Tools/downcast.hpp"

namespace
{
std::vector<pyaf::downcast_step>&
steps()
{
    static std::vector<pyaf::downcast_step> s; // filled at import (GIL held), read-only afterwards
    return s;
}
} // namespace

void
pyaf::add_module_class(downcast_step step)
{
    steps().push_back(step);
}

std::size_t
pyaf::n_module_classes()
{
    return steps().size();
}

const void*
pyaf::downcast_module(const spu::module::Module* m, const std::type_info*& type)
{
    // recorded bases first: the first match from the end is the most derived recorded class of m
    auto& s = steps();
    for (auto it = s.rbegin(); it != s.rend(); ++it)
        if (auto p = (*it)(m, type)) return p;
    return nullptr;
}

bool
pyaf::register_module_downcaster()
{
#ifdef PYAF_HAS_STREAMPU_DOWNCAST_REGISTRY
    pyspu::register_module_downcaster(&pyaf::downcast_module);
    return true;
#else
    return false;
#endif
}
