#include "native-overrides/heap_partitions.hpp"
#include <cassert>
#include <cstring>
#include <iostream>
#include <limits>

int main() {
    using mw34::heap_partitions::GuestHeap;
    GuestHeap heap;
    std::map<unsigned, std::vector<unsigned char>> memory;
    unsigned commits = 0, clears = 0, checks = 0;
    auto check = [&](bool value) {
        ++checks;
        if (!value)
            throw std::runtime_error("Heap partition check failed");
    };
    auto commit = [&](unsigned at, unsigned bytes) {
        check(!memory.count(at));
        memory.emplace(at, std::vector<unsigned char>(bytes));
        ++commits;
    };
    auto clear = [&](unsigned at, unsigned bytes) {
        auto base = heap.region_of(at);
        // New regions are committed before publication of their metadata.
        if (!base) {
            auto it = memory.upper_bound(at);
            --it;
            base = it->first;
        }
        auto &data = memory.at(base);
        check(std::uint64_t(at - base) + bytes <= data.size());
        std::fill_n(data.begin() + (at - base), bytes, 0);
        ++clears;
    };
    auto allocate = [&](unsigned bytes, bool zero, unsigned owner) {
        return heap.allocate(bytes, zero, owner, commit, clear);
    };
    constexpr unsigned crt = 0x31415920, codec = 0x3f400010, services = 0;

    const auto video = allocate(0x1d1e8, false, codec);
    std::fill(memory.at(video).begin(), memory.at(video).end(), 0xab);
    heap.release(video);
    const auto menu = allocate(0x17730, false, crt);
    check(menu != video);
    check(heap.owner_of(menu) == crt && heap.owner_of(video) == codec);
    check(memory.at(menu).at(0x16fa0) == 0);
    const auto codec_again = allocate(0x17730, false, codec);
    check(codec_again == video && memory.at(video).at(0x16fa0) == 0xab);
    check(clears == 0); // No blanket zero-fill to conceal stale data.
    heap.release(codec_again);
    const auto codec_zero = allocate(0x17730, true, codec);
    check(codec_zero == video && memory.at(video).at(0x16fa0) == 0);
    check(clears == 1);

    const auto environment = allocate(5000, false, services);
    check(heap.owner_of(environment) == services);
    check(heap.destroy(crt) == 1);
    check(!heap.live.count(menu) && heap.live.count(environment) && heap.live.count(codec_zero));
    check(allocate(0x17730, false, crt) == menu);
    check(heap.destroy(codec) == 1 && heap.live.count(environment));

    const auto a = allocate(17, false, services), b = allocate(31, false, services);
    check(b == a + 32 && heap.live.at(a) == 17 && heap.live.at(b) == 31);
    heap.release(a);
    heap.release(b);
    check(allocate(64, false, services) == a);
    const auto z = allocate(0, true, services);
    check(z && heap.live.at(z) == 0 && !(z & 15));
    heap.release(z);
    bool rejected = false;
    try {
        heap.release(z);
    } catch (const std::runtime_error &) {
        rejected = true;
    }
    check(rejected);
    const auto count = heap.live.size();
    const auto before = commits;
    check(allocate(std::numeric_limits<unsigned>::max(), false, codec) == 0);
    check(heap.live.size() == count && commits == before);

    // Alternating domains use parked tails only within their original heap.
    for (unsigned i = 0; i < 60; ++i) {
        const unsigned owner = i % 3 == 0 ? crt : i % 3 == 1 ? codec : services;
        const auto at = allocate(4097 + i * 16, false, owner);
        check(at && heap.owner_of(at) == owner);
        for (const auto &[other, size] : heap.live)
            if (other != at) {
                check(std::uint64_t(at) + heap.live.at(at) <= other ||
                      std::uint64_t(other) + size <= at);
            }
    }
    GuestHeap exhausted;
    exhausted.top = exhausted.mapped = exhausted.region_end = GuestHeap::hi;
    bool touched = false;
    check(exhausted.allocate(
              1, false, crt, [&](unsigned, unsigned) { touched = true; }, clear) == 0 &&
          !touched);
    std::cout << "heap partitions checks=" << checks << " failures=0\n";
}
