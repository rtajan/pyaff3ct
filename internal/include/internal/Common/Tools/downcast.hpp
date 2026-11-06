/*!
 * \file
 * \brief Typing of the AFF3CT modules returned by pystreampu (Plan.md, rule R8 bis).
 *
 * pybind11 types a returned `spu::module::Module*` after its dynamic type; most concrete AFF3CT classes are not
 * registered (factory-only classes, concrete classes not wrapped yet), so the object would fall back to `Module`.
 * Every module class registered by pyaff3ct is recorded here (base classes first, as pybind11 requires), and one
 * downcaster, registered in the pystreampu registry, returns the most derived recorded class of an object.
 *
 * The registry exists in pystreampu >= the version that ships "wrapper/Common/Tools/Module_downcast.hpp"
 * (`PYAF_HAS_STREAMPU_DOWNCAST_REGISTRY`); with an older pystreampu the classes are still recorded but nothing is
 * registered (the modules returned by streampu are then typed `Module`).
 */
#ifndef PYAF_COMMON_TOOLS_DOWNCAST_HPP_
#define PYAF_COMMON_TOOLS_DOWNCAST_HPP_

#include <typeinfo>

#include <Module/Module.hpp>

#if __has_include("wrapper/Common/Tools/Module_downcast.hpp")
#include "wrapper/Common/Tools/Module_downcast.hpp"
#define PYAF_HAS_STREAMPU_DOWNCAST_REGISTRY 1
#endif

namespace pyaf
{
//! Pointer to the `T` sub-object of `m` (and `type` = typeid(T)) if `m` is a `T`, nullptr otherwise.
using downcast_step = const void* (*)(const spu::module::Module* m, const std::type_info*& type);

template<class T>
const void*
downcast_step_to(const spu::module::Module* m, const std::type_info*& type)
{
    if (auto p = dynamic_cast<const T*>(m))
    {
        type = &typeid(T);
        return p;
    }
    return nullptr;
}

//! Records a registered module class (call it right after its `py::class_`, bases first).
void
add_module_class(downcast_step step);

template<class T>
void
add_module_class()
{
    add_module_class(&downcast_step_to<T>);
}

//! Number of recorded module classes.
std::size_t
n_module_classes();

//! Most derived recorded class of `m` (nullptr if `m` is not an AFF3CT module).
const void*
downcast_module(const spu::module::Module* m, const std::type_info*& type);

//! Registers `downcast_module` in the pystreampu registry (once, after every class is recorded); false if the
//! installed pystreampu has no registry.
bool
register_module_downcaster();
} // namespace pyaf

#endif // PYAF_COMMON_TOOLS_DOWNCAST_HPP_
