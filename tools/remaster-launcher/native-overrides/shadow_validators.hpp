#pragma once
#include <cstdint>
#include <functional>
#include <limits>
#include <stdexcept>
#include <utility>
#include <vector>

namespace mw34::submission {
// Most draws have no retained-world proof. Keep callbacks in scene-owned storage
// so each ordinary draw carries an index rather than an empty std::function.
// Copy the callback into a retained caster before the scene can be destroyed.
class ShadowValidators {
  public:
    using Callback = std::function<bool()>;
    static constexpr std::uint32_t none = (std::numeric_limits<std::uint32_t>::max)();

  private:
    std::vector<Callback> values;

  public:
    std::uint32_t capture(Callback callback) {
        if (!callback)
            return none;
        if (values.size() >= none)
            throw std::runtime_error("Shadow validation storage capacity exceeded");
        const auto index = std::uint32_t(values.size());
        values.push_back(std::move(callback));
        return index;
    }
    bool has(std::uint32_t index) const {
        return index != none && bool(values.at(index));
    }
    const Callback &get(std::uint32_t index) const {
        static const Callback empty;
        return index == none ? empty : values.at(index);
    }
    std::size_t size() const { return values.size(); }
};
} // namespace mw34::submission
