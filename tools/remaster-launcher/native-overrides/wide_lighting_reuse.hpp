#pragma once
#include "exact_shared_value.hpp"
#include <cstdint>
#include <memory>

namespace mw34::submission {
// Separate sun/sky runs retain every adjusted camera/projection bit. Draws own
// their immutable values, so later cache replacement or scene destruction cannot
// invalidate an earlier draw. No original geometry or transform is skipped.
template<class View> class WideLightingViews {
    ExactSharedValue<View> sun_values,sky_values;
    const View* last_sun{};
    const View* last_sky{};
  public:
    std::uint64_t captures{},allocations{};
    std::shared_ptr<const View> capture(const View& value,bool sky) {
        auto result=(sky?sky_values:sun_values).capture(value);
        auto& previous=sky?last_sky:last_sun;
        ++captures;
        if(result.get()!=previous){++allocations;previous=result.get();}
        return result;
    }
};
}
