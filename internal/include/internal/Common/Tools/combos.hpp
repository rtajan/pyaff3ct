/*!
 * \file
 * \brief Type lists used to register every dtype combination compiled by AFF3CT.
 *
 * The combinations themselves are generated in "internal/Generated/instantiations.hpp" from the AFF3CT API
 * fingerprint (scripts/gen_instantiations.py): `pyaf::gen::Module_Encoder` is for instance
 * `combos<types<int8_t>, types<int16_t>, types<int32_t>, types<int64_t>>`.
 */
#ifndef PYAF_COMMON_TOOLS_COMBOS_HPP_
#define PYAF_COMMON_TOOLS_COMBOS_HPP_

#include <cstddef>
#include <tuple>

namespace pyaf
{
//! One combination of template arguments, e.g. `types<int32_t, float>` for `Decoder_SIHO<B, R>`.
template<typename... Ts>
struct types
{
    static constexpr std::size_t size = sizeof...(Ts);
    template<std::size_t I>
    using at = std::tuple_element_t<I, std::tuple<Ts...>>;
};

//! A list of combinations.
template<typename... Cs>
struct combos
{
    static constexpr std::size_t size = sizeof...(Cs);
};

/*!
 * \brief Calls `f(types<...>{})` for each combination of `Combos`.
 *
 * \code
 * pyaf::for_each_combo<pyaf::gen::Module_Encoder>(
 *   [&](auto c) { using C = decltype(c); wrap_encoder<typename C::template at<0>>(scope); });
 * \endcode
 */
template<typename Combos, typename F>
void
for_each_combo(F&& f);

template<typename... Cs, typename F>
void
for_each_combo_impl(combos<Cs...>, F&& f)
{
    (f(Cs{}), ...);
}

template<typename Combos, typename F>
void
for_each_combo(F&& f)
{
    for_each_combo_impl(Combos{}, std::forward<F>(f));
}
} // namespace pyaf

#endif // PYAF_COMMON_TOOLS_COMBOS_HPP_
