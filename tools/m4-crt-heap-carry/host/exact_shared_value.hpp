#pragma once
#include <cstring>
#include <memory>
#include <type_traits>

namespace mw34::submission {
// Share identical immutable payloads after their caller has validated them.
// Compare object bytes rather than floating-point equality: signed zero and
// every projection/camera bit remain distinct. Earlier draws retain ownership.
template<class Value> class ExactSharedValue {
    static_assert(std::is_trivially_copyable_v<Value>);
    std::shared_ptr<const Value> previous;
public:
    std::shared_ptr<const Value> capture(const Value& value) {
        if (!previous || std::memcmp(previous.get(), &value, sizeof(Value)))
            previous = std::make_shared<const Value>(value);
        return previous;
    }
};
} // namespace mw34::submission
