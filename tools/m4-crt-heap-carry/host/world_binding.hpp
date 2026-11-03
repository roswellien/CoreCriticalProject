#pragma once
#include <cstdint>
#include <map>
#include <memory>
#include <optional>
#include <stdexcept>
#include <vector>

namespace mw34::world {
// The caller supplies a freshly read source snapshot. Addresses are lookup
// hints only; exact source bytes establish whether a decoded mesh can be reused.
// The caller serializes cache mutation and lookup; this class owns no locks.
// Shared snapshots remain charged while deferred draws or completed frames retain
// them. The budget includes those owners, not only the cache's current entries.
struct SnapshotBudget {
    std::size_t entries{}, bytes{}, maximum_entries{}, maximum_bytes{};
};
struct SourceCharge {
    std::shared_ptr<SnapshotBudget> budget;
    std::size_t charged_bytes;
    SourceCharge(std::shared_ptr<SnapshotBudget> owner, std::size_t bytes)
        : budget(std::move(owner)), charged_bytes(bytes) {
        ++budget->entries;
        budget->bytes += bytes;
    }
    SourceCharge(const SourceCharge &) = delete;
    SourceCharge &operator=(const SourceCharge &) = delete;
    ~SourceCharge() {
        --budget->entries;
        budget->bytes -= charged_bytes;
    }
};
struct SourceBytes : SourceCharge {
    std::vector<unsigned char> bytes;
    SourceBytes(std::shared_ptr<SnapshotBudget> owner, std::vector<unsigned char> data)
        : SourceCharge(std::move(owner), data.size()), bytes(std::move(data)) {}
};

template <class T> class SnapshotCache {
    struct Entry {
        std::shared_ptr<const SourceBytes> source;
        std::shared_ptr<const T> value;
    };
    std::map<std::uint32_t, Entry> entries_;
    std::shared_ptr<SnapshotBudget> budget_;
    std::shared_ptr<const SourceBytes> retain(std::vector<unsigned char> bytes,
                                              const SourceBytes *credit) {
        const auto credited_bytes = credit ? credit->bytes.size() : 0;
        const auto credited_entries = credit ? 1U : 0U;
        if (budget_->entries - credited_entries >= budget_->maximum_entries ||
            bytes.size() > budget_->maximum_bytes - (budget_->bytes - credited_bytes))
            throw std::runtime_error("World snapshot cache capacity exceeded");
        return std::make_shared<const SourceBytes>(budget_, std::move(bytes));
    }

  public:
    SnapshotCache(std::size_t entries, std::size_t bytes)
        : budget_(std::make_shared<SnapshotBudget>(SnapshotBudget{0, 0, entries, bytes})) {}
    std::shared_ptr<const T> find(std::uint32_t key,
                                  const std::vector<unsigned char> &bytes) const {
        const auto found = entries_.find(key);
        return found != entries_.end() && found->second.source->bytes == bytes ? found->second.value
                                                                               : nullptr;
    }
    void put(std::uint32_t key, std::vector<unsigned char> bytes, std::shared_ptr<const T> value) {
        if (!value)
            throw std::runtime_error("World snapshot cache cannot store an empty value");
        const auto previous = entries_.find(key);
        const SourceBytes *credit =
            previous != entries_.end() && previous->second.source.use_count() == 1
                ? previous->second.source.get()
                : nullptr;
        auto snapshot = retain(std::move(bytes), credit);
        entries_.insert_or_assign(key, Entry{std::move(snapshot), std::move(value)});
    }
    std::shared_ptr<const SourceBytes> source(std::uint32_t key) const {
        return entries_.at(key).source;
    }
    std::shared_ptr<const SourceBytes> retain(std::vector<unsigned char> bytes) {
        return retain(std::move(bytes), nullptr);
    }
    std::shared_ptr<const SourceCharge> charge(std::size_t bytes) {
        if (budget_->entries >= budget_->maximum_entries ||
            bytes > budget_->maximum_bytes - budget_->bytes)
            throw std::runtime_error("World snapshot cache capacity exceeded");
        return std::make_shared<const SourceCharge>(budget_, bytes);
    }
    void clear() { entries_.clear(); }
    std::size_t size() const { return entries_.size(); }
    std::size_t bytes() const { return budget_->bytes; }
};

inline std::optional<std::size_t> polygon_slot(std::uint32_t base, std::size_t count,
                                               std::uint32_t address) {
    // Original polygon records have a 36-byte stride. Reject earlier, misaligned
    // and one-past addresses using widened arithmetic, without reading memory.
    // The caller remains responsible for the source array's ownership and count.
    if (address < base)
        return {};
    const auto byte_offset = std::uint64_t(address) - base;
    if (byte_offset % 36 || byte_offset / 36 >= count)
        return {};
    return std::size_t(byte_offset / 36);
}
} // namespace mw34::world
