#include "../m4-crt-heap-carry/host/heap_partitions.hpp"
#include <cassert>
#include <cstring>
#include <iostream>
#include <limits>
#include <random>

namespace {
// The region map search contains() used before the slot table, kept as the reference.
bool reference_contains(const std::map<unsigned, unsigned> &regions, unsigned address,
                        unsigned bytes) {
    auto region = regions.upper_bound(address);
    if (region == regions.begin())
        return false;
    --region;
    return region->first != 0 && address < region->second &&
           std::uint64_t(address) + bytes <= region->second;
}
void run_heap_partition_checks() {
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
        std::fill_n(data.begin() + (at - base), bytes, static_cast<unsigned char>(0));
        ++clears;
    };
    auto allocate = [&](unsigned bytes, bool zero, unsigned owner) {
        return heap.allocate(bytes, zero, owner, commit, clear);
    };
    constexpr unsigned crt = 0x31415920, codec = 0x3f400010, services = 0;

    check(!heap.contains(GuestHeap::lo, 0));
    check(!heap.contains(GuestHeap::lo, 1));
    GuestHeap boundaries;
    constexpr unsigned first = GuestHeap::lo, second = first + 0x20000;
    boundaries.add_region(first, first + 0x10000);
    boundaries.add_region(second, second + 0x10000);
    boundaries.add_region(second + 0x10000, second + 0x20000);
    boundaries.region_owners = {{first, crt}, {second, codec}, {second + 0x10000, services}};
    struct RangeCase {
        unsigned address, bytes;
        bool expected;
    };
    const RangeCase ranges[] = {
        {0, 0, false},
        {first - 1, 1, false},
        {first, 0, true},
        {first, 0x10000, true},
        {first, 0x10001, false},
        {first + 0xffff, 0, true},
        {first + 0xffff, 1, true},
        {first + 0xffff, 2, false},
        {first + 0x10000, 0, false},
        {first + 0x10000, 1, false},
        {second - 1, 1, false},
        {second, 0, true},
        {second, 0x10000, true},
        {second, 0x10001, false},
        {second + 0xffff, 2, false},
        {second + 0x10000, 0, true},
        {second + 0x10000, 0x10000, true},
        {second + 0x20000, 0, false},
        {second + 0x20000, 1, false},
        {first, std::numeric_limits<unsigned>::max(), false},
        {std::numeric_limits<unsigned>::max(), 0, false},
        {std::numeric_limits<unsigned>::max(), 1, false},
    };
    for (const auto &range : ranges)
        check(boundaries.contains(range.address, range.bytes) == range.expected);
    check(boundaries.owner_of(first) == crt && boundaries.owner_of(second) == codec);
    // A lookup must reflect region edits immediately, without retaining an iterator.
    boundaries.erase_region(second);
    check(!boundaries.contains(second, 1));
    boundaries.add_region(second, second + 0x10000);
    check(boundaries.contains(second, 0x10000) && !boundaries.contains(second, 0x10001));
    // A region spanning two slots answers for both; the old neighbor's end is gone.
    boundaries.erase_region(second + 0x10000);
    boundaries.erase_region(second);
    boundaries.add_region(second, second + 0x20000);
    check(boundaries.contains(second, 0x20000) && boundaries.contains(second + 0x18000, 0x8000));
    check(!boundaries.contains(second, 0x20001) && !boundaries.contains(second + 0x20000, 0));
    boundaries.clear_regions();
    check(!boundaries.contains(first, 1) && !boundaries.contains(second, 1));

    // add_region accepts only regions allocate can make: 64 KiB-aligned, inside
    // the window, and sharing no byte with another region.
    GuestHeap rejecting;
    constexpr unsigned taken = first + 0x100000, taken_end = first + 0x200000;
    rejecting.add_region(taken, taken_end);
    struct RejectedRegion {
        unsigned start, end;
    };
    const RejectedRegion rejected_regions[] = {
        {0, 0x10000},                                       // start 0, the old map sentinel
        {first + 0x10, first + 0x10000},                    // unaligned start
        {first, first + 0x10010},                           // unaligned end
        {first - 0x10000, first},                           // below the window
        {GuestHeap::hi - 0x10000, GuestHeap::hi + 0x10000}, // past the window
        {first + 0x20000, first + 0x20000},                 // empty
        {first + 0x30000, first + 0x20000},                 // reversed
        {taken, taken + 0x10000},                           // same start
        {taken - 0x10000, taken + 0x10000},                 // overlaps the start
        {taken_end - 0x10000, taken_end + 0x10000},         // overlaps the end
        {taken + 0x10000, taken + 0x20000},                 // inside
        {first, taken_end + 0x100000},                      // covers it
    };
    for (const auto &region : rejected_regions) {
        bool threw = false;
        try {
            rejecting.add_region(region.start, region.end);
        } catch (const std::runtime_error &) {
            threw = true;
        }
        check(threw);
    }
    check(rejecting.regions().size() == 1);
    // Neighbors that touch without overlapping are accepted.
    rejecting.add_region(taken - 0x10000, taken);
    rejecting.add_region(taken_end, taken_end + 0x10000);
    check(rejecting.regions().size() == 3);

    // The slot table must answer exactly as the map search did, for any set of
    // regions allocate can make. The seed is fixed so a failure repeats.
    std::mt19937 random(244);
    auto random_between = [&](unsigned low, unsigned high) {
        return std::uniform_int_distribution<unsigned>(low, high)(random);
    };
    constexpr unsigned slot = GuestHeap::slot_bytes;
    for (unsigned set = 0; set < 500; ++set) {
        GuestHeap random_heap;
        std::vector<unsigned> region_edges;
        const unsigned region_count = random_between(1, 200);
        unsigned next_start = GuestHeap::lo + random_between(0, 16) * slot;
        while (random_heap.regions().size() < region_count) {
            const unsigned size = random_between(1, 64) * slot; // 64 KiB to 4 MiB
            if (std::uint64_t(next_start) + size > GuestHeap::hi)
                break;
            random_heap.add_region(next_start, next_start + size);
            region_edges.push_back(next_start);
            region_edges.push_back(next_start + size);
            const unsigned gap = random_between(0, 16) * slot; // 0 to 1 MiB
            next_start += size + gap;
        }
        const unsigned last_edge = unsigned(region_edges.size()) - 1;
        for (unsigned query = 0; query < 2000; ++query) {
            const unsigned edge = region_edges[random_between(0, last_edge)];
            const unsigned slot_start =
                GuestHeap::lo + random_between(0, GuestHeap::slot_count - 1) * slot;
            unsigned address = 0;
            switch (random_between(0, 5)) {
            case 0:
                address = edge;
                break;
            case 1:
                address = edge - 1;
                break;
            case 2:
                address = slot_start;
                break;
            case 3:
                address = slot_start + slot - 1;
                break;
            case 4:
                address = random_between(GuestHeap::lo, GuestHeap::hi - 1);
                break;
            default:
                address = random_between(0, std::numeric_limits<unsigned>::max());
                break;
            }
            unsigned bytes = 0;
            switch (random_between(0, 4)) {
            case 0:
                bytes = 0;
                break;
            case 1:
                bytes = 1;
                break;
            case 2:
                bytes = random_between(0, 0x400000);
                break;
            case 3:
                bytes = std::numeric_limits<unsigned>::max();
                break;
            default:
                bytes = edge - address; // reaches a region edge exactly, or wraps
                break;
            }
            check(random_heap.contains(address, bytes) ==
                  reference_contains(random_heap.regions(), address, bytes));
        }
    }

    const auto video = allocate(0x1d1e8, false, codec);
    std::fill(memory.at(video).begin(), memory.at(video).end(), static_cast<unsigned char>(0xab));
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
} // namespace

// Report a failed check as an ordinary test failure. An uncaught exception
// aborts, and a Debug build then waits on an error dialog instead of exiting.
int main() {
    try {
        run_heap_partition_checks();
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
