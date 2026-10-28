#pragma once
#include <cstddef>
#include <cstring>
#include <stdexcept>
#include <memory>
#include <vector>

namespace mw34::textures {
// Unlocked DirectDraw texture pixels belong to the 64-bit host. Guest-address
// mappings are temporary Lock views, never persistent texture storage.
class Backing {
    std::shared_ptr<std::vector<unsigned char>> pixels_;
    void check(std::size_t offset, std::size_t bytes) const {
        const auto size = pixels_ ? pixels_->size() : 0;
        if (offset > size || bytes > size - offset)
            throw std::out_of_range("Texture pixel transfer outside its surface");
    }
  public:
    void resize(std::size_t bytes) { pixels_ = std::make_shared<std::vector<unsigned char>>(bytes); }
    bool empty() const { return !pixels_ || pixels_->empty(); }
    void clear() { pixels_.reset(); }
    void read(std::size_t offset, void* out, std::size_t bytes) const {
        check(offset, bytes);
        if (bytes) std::memcpy(out, pixels_->data() + offset, bytes);
    }
    void write(std::size_t offset, const void* in, std::size_t bytes) {
        check(offset, bytes);
        if (!bytes) return;
        // Texture2::Load may share identical pixels. Any later write detaches,
        // preserving independent source/destination surface contents.
        if (pixels_.use_count() != 1) pixels_ = std::make_shared<std::vector<unsigned char>>(*pixels_);
        std::memmove(pixels_->data() + offset, in, bytes);
    }
};
}
