#pragma once

#include <cstddef>
#include <stdexcept>
#include <string>
#include <vector>

namespace mw34 {

// Labels are owned by Host's stable deque and outlive this log. Share those
// labels and allocate text only for per-call annotations. Index chronologically.
class ServiceHistory {
    struct Entry {
        const std::string* label{};
        std::string annotation;
        Entry& operator+=(const std::string& suffix) { annotation += suffix; return *this; }
        std::string text() const { return label ? *label + annotation : annotation; }
    };
    std::vector<Entry> entries_;
    std::size_t first_{};
    std::size_t limit_;

public:
    explicit ServiceHistory(std::size_t limit = 400000) : limit_(limit) {
        if (!limit) throw std::invalid_argument("Service history must retain records");
    }
    std::size_t size() const { return entries_.size(); }
    bool empty() const { return entries_.empty(); }
    void push_back(const std::string* value) {
        if (!value) throw std::invalid_argument("Missing service label");
        if (entries_.size() < limit_) {
            entries_.push_back({value, {}});
        } else {
            entries_[first_].label = value;
            entries_[first_].annotation.clear();
            if (++first_ == limit_) first_ = 0;
        }
    }
    // Thread-exit summaries have unique text rather than an interned label.
    void push_back(std::string value) {
        if (entries_.size() < limit_) entries_.push_back({nullptr, std::move(value)});
        else {
            entries_[first_].label = nullptr;
            entries_[first_].annotation = std::move(value);
            if (++first_ == limit_) first_ = 0;
        }
    }
    std::string operator[](std::size_t index) const {
        const auto at = first_ + index;
        return entries_[at >= limit_ ? at - limit_ : at].text();
    }
    Entry& back() {
        return entries_[first_ ? first_ - 1 : entries_.size() - 1];
    }
    operator std::vector<std::string>() const {
        std::vector<std::string> result;
        result.reserve(size());
        for (std::size_t i = 0; i < size(); ++i) result.push_back((*this)[i]);
        return result;
    }
};

} // namespace mw34
