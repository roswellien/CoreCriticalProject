#pragma once

#include "surface_materials.hpp"
#include "platform/sha256.hpp"

#include <filesystem>
#include <fstream>
#include <map>
#include <tuple>

namespace mw34::materials {

// The environment parser supplies a contained path from a declared pack member.
struct StreamedHeightPin {
    std::filesystem::path path;
    std::string sha256;
    std::uint32_t width{}, height{};
    std::uint64_t bytes{};
};

// Producer-owned cache. Frame packets keep immutable image handles alive
// independently of cache residency, including across subset changes.
class StreamedHeightCache {
  public:
    using Image = std::shared_ptr<const SurfaceMaterialImage>;

    StreamedHeightCache(std::shared_ptr<SurfaceDecodedBudget> budget,
                        std::vector<StreamedHeightPin> pins)
        : budget_(std::move(budget)), pins_(std::move(pins)) {
        if (!budget_ || pins_.size() > 512)
            throw std::runtime_error("Invalid streamed height inventory");
        std::map<Key, std::filesystem::path> paths;
        for (const auto &pin : pins_) {
            if (pin.path.empty() || pin.sha256.size() != 64 ||
                pin.sha256.find_first_not_of("0123456789abcdef") != std::string::npos ||
                !pin.width || !pin.height || pin.width > max_surface_dimension ||
                pin.height > max_surface_dimension ||
                pin.bytes != std::uint64_t(pin.width) * pin.height)
                throw std::runtime_error("Invalid streamed height image pin");
            const auto [entry, inserted] = paths.emplace(key(pin), pin.path);
            if (!inserted && entry->second != pin.path)
                throw std::runtime_error("Duplicate streamed height payload path");
        }
    }

    // Call before admitting the next subset. Ordering of requests is decided by
    // the producer. Outstanding frame owners can still be reused after eviction.
    void select(const std::vector<std::size_t> &ids) {
        std::set<Key> wanted;
        for (const auto id : ids)
            wanted.insert(key(pins_.at(id)));
        for (auto it = resident_.begin(); it != resident_.end();) {
            if (wanted.count(it->first))
                ++it;
            else
                it = resident_.erase(it);
        }
        wanted_.swap(wanted);
    }

    Image find(std::size_t id) const {
        const auto it = resident_.find(key(pins_.at(id)));
        return it == resident_.end() ? Image{} : it->second;
    }

    // An empty result indicates temporary decoded-budget pressure. Corrupt
    // payloads throw before publication and release their reservation.
    Image acquire(std::size_t id) {
        const auto &pin = pins_.at(id);
        const auto identity = key(pin);
        if (!wanted_.count(identity))
            throw std::runtime_error("Streamed height image is outside the selected subset");
        if (const auto resident = resident_.find(identity); resident != resident_.end())
            return resident->second;
        if (const auto prior = owners_.find(identity); prior != owners_.end())
            if (auto image = prior->second.lock()) {
                resident_.emplace(identity, image);
                return image;
            }

        auto payload = std::make_shared<Payload>(budget_);
        if (!payload->reservation.try_grow(pin.bytes))
            return {};
        std::ifstream input(pin.path, std::ios::binary);
        if (!input)
            throw std::runtime_error("Cannot open streamed height payload");
        auto &image = payload->image;
        image.pixels.resize(static_cast<std::size_t>(pin.bytes));
        if (!input.read(reinterpret_cast<char *>(image.pixels.data()),
                        static_cast<std::streamsize>(pin.bytes)) ||
            input.peek() != std::char_traits<char>::eof() || input.bad())
            throw std::runtime_error("Streamed height payload size mismatch");
        ::platform::integrity::Sha256 digest;
        digest.update(image.pixels.data(), image.pixels.size());
        if (digest.hex() != pin.sha256)
            throw std::runtime_error("Streamed height payload SHA-256 mismatch");

        image.name = pin.sha256;
        image.width = pin.width;
        image.height = pin.height;
        image.role = surface_role_height;
        image.hash = normal_hash(image.pixels.data(), image.pixels.size());
        Image verified(payload, &image);
        owners_.insert_or_assign(identity, verified);
        resident_.emplace(identity, verified);
        return verified;
    }

  private:
    using Key = std::tuple<std::string, std::uint32_t, std::uint32_t>;

    static Key key(const StreamedHeightPin &pin) {
        return {pin.sha256, pin.width, pin.height};
    }

    struct Payload {
        explicit Payload(const std::shared_ptr<SurfaceDecodedBudget> &budget)
            : reservation(budget) {}
        SurfaceDecodedReservation reservation;
        SurfaceMaterialImage image;
    };

    std::shared_ptr<SurfaceDecodedBudget> budget_;
    std::vector<StreamedHeightPin> pins_;
    std::set<Key> wanted_;
    std::map<Key, Image> resident_;
    std::map<Key, std::weak_ptr<const SurfaceMaterialImage>> owners_;
};

} // namespace mw34::materials
