#include "admission.hpp"
#include "data_imports.hpp"
#include <cstring>
#include <fstream>
#include <iostream>
using namespace mw34;
using namespace mw34::m4_runtime;
namespace cd = mw34::m4_crt_data;
namespace {
unsigned checks{};
std::vector<std::byte> provider, game, raw;
void check(bool b, const char *w) {
    if (!b)
        throw std::runtime_error(w);
    ++checks;
}
std::vector<std::byte> file(const char *p) {
    std::ifstream f(p, std::ios::binary | std::ios::ate);
    check(bool(f), "Private test input required");
    const auto n = f.tellg();
    check(n > 0 && n < 64 * 1024 * 1024, "Private test input bounded");
    std::vector<std::byte> b(static_cast<std::size_t>(n));
    f.seekg(0);
    f.read(reinterpret_cast<char *>(b.data()), static_cast<std::streamsize>(b.size()));
    check(bool(f), "Private test input read");
    return b;
}
std::uint32_t word(std::span<const std::byte> b, unsigned o) {
    check(std::uint64_t{o} + 4 <= b.size(), "Reference header bounds");
    std::uint32_t x{};
    for (unsigned i = 0; i < 4; ++i)
        x |= std::to_integer<std::uint32_t>(b[o + i]) << (8 * i);
    return x;
}
Policy policy() {
    Policy p;
    p.stack_bytes = p.heap_bytes = 8192;
    return p;
}
cd::ReferenceProjection projection() {
    check(raw.size() > 44 && std::memcmp(raw.data(), "MW4CMD01", 8) == 0 && word(raw, 8) == 1 &&
              word(raw, 12) == 192,
          "Actual frozen measurement header");
    const auto size = word(raw, 20), path = word(raw, 36), regions = word(raw, 40);
    const std::uint64_t offset = 44 + path + 64 + 28 + 28ULL * regions;
    check(size && size <= 131072 && offset + size <= raw.size(),
          "Actual external input buffer extent");
    cd::ReferenceProjection p;
    p.observed_original_pointer = word(raw, 32);
    p.owned_guest_pointer = GuestAddress{0x32001000};
    p.observed_buffer.assign(raw.begin() + static_cast<std::ptrdiff_t>(offset),
                             raw.begin() + static_cast<std::ptrdiff_t>(offset + size));
    p.original_buffer_sha256 = m4::sha256(p.observed_buffer);
    p.original_measurement_sha256 =
        "2a9ed0395eaba271b317797525d699de3dd099be8f80a91921059637f546863f";
    return p;
}
m4::LoadedImage fixture(const char *library = "MSVCRT.dll", const char *name = "_acmdln",
                        bool duplicate = false) {
    m4::LoadedImage x;
    x.metadata.image_base = 0x400000;
    x.metadata.entry_point = GuestAddress{0x401000};
    x.memory.map(GuestAddress{0x401000}, 4096, Permissions::read | Permissions::execute);
    x.metadata.mapped_regions = {
        {"authored", GuestAddress{0x401000}, 4096, Permissions::read | Permissions::execute}};
    x.memory.map(GuestAddress{0x5bb000}, 4096, Permissions::read | Permissions::write);
    for (auto [slot, label] : std::array<std::pair<unsigned, const char *>, 2>{
             {{0x5bb518, name}, {0x5bb508, "_adjust_fdiv"}}}) {
        m4::ImportSymbol i;
        i.library = library;
        i.name = label;
        i.iat_rva = slot - 0x400000;
        i.original_iat_value = 0xabcdef00 + slot;
        x.memory.store<std::uint32_t>(GuestAddress{slot}, i.original_iat_value);
        x.metadata.imports.push_back(i);
    }
    if (duplicate)
        x.metadata.imports.push_back(x.metadata.imports[0]);
    x.memory.protect(GuestAddress{0x5bb000}, Permissions::read);
    return x;
}
template <class F> void reject(F fn, cd::DataFaultReason reason, cd::DataImportRegistry &r) {
    try {
        fn();
    } catch (const cd::DataFault &f) {
        check(f.reason == reason && r.poisoned() && r.first_fault().has_value(),
              "Exact retained typed data denial");
        return;
    }
    throw std::runtime_error("Data observer accepted required failure");
}
void tests() {
    {
        auto r = Runtime::from_admitted_image(game, policy());
        const auto original = r.memory().load<std::uint32_t>(GuestAddress{0x5bb518});
        cd::DataImportRegistry d(r);
        auto p = projection();
        const auto bytes = p.observed_buffer;
        d.admit_reference_projection(provider, p);
        check(d.record() && d.record()->reference_projection_ready &&
                  d.record()->reference_projection_only &&
                  !d.record()->production_initialized_service,
              "Completed reference projection cannot advertise production service");
        check(d.resolve_reference_load32(GuestAddress{0x5bb518}) == 0x78037174 &&
                  r.memory().load<std::uint32_t>(GuestAddress{0x78037174}) == 0x32001000,
              "Declared real named IAT resolves owned provider/global/guest pointer");
        std::vector<std::byte> b(bytes.size());
        r.memory().read(GuestAddress{0x32001000}, b);
        check(b == bytes && r.memory().load<std::uint32_t>(GuestAddress{0x5bb518}) == original,
              "Owning guest bytes and original raw IAT preservation");
        bool ro{};
        try {
            r.memory().store<std::uint8_t>(GuestAddress{0x32001000}, 0);
        } catch (const MemoryFault &f) {
            ro = f.reason() == MemoryFaultReason::permission_denied;
        }
        check(ro, "Projected guest buffer initially readonly");
    }
    for (unsigned c = 0; c < 8; ++c) {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        cd::DataImportRegistry d(r);
        auto p = projection();
        if (c == 0)
            p.observed_original_pointer = 0;
        if (c == 1)
            p.observed_buffer.clear();
        if (c == 2)
            p.observed_buffer.back() = std::byte{1};
        if (c == 3)
            p.observed_buffer[0] = std::byte{};
        if (c == 4)
            p.original_buffer_sha256 = std::string(64, '0');
        if (c == 5)
            p.original_measurement_sha256 = std::string(64, '0');
        if (c == 6)
            p.owned_guest_pointer = GuestAddress{0x31ffffff};
        if (c == 7)
            p.owned_guest_pointer = GuestAddress{0x32fffffc};
        reject([&] { d.admit_reference_projection(provider, p); },
               cd::DataFaultReason::invalid_admission, d);
        check(!d.record() || !d.record()->reference_projection_ready,
              "Denied projection never becomes ready");
    }
    for (unsigned c = 0; c < 3; ++c) {
        auto r = Runtime::for_authored_fixture(
            fixture(c == 0 ? "OTHER.dll" : "MSVCRT.dll", c == 1 ? "OTHER" : "_acmdln", c == 2),
            policy());
        cd::DataImportRegistry d(r);
        reject([&] { d.admit_reference_projection(provider, projection()); },
               cd::DataFaultReason::invalid_admission, d);
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        cd::DataImportRegistry d(r);
        auto changed = provider;
        changed[100] ^= std::byte{1};
        reject([&] { d.admit_reference_projection(changed, projection()); },
               cd::DataFaultReason::invalid_admission, d);
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        r.memory().map(GuestAddress{0x32001000}, 4096, Permissions::read | Permissions::write);
        r.memory().store<std::uint32_t>(GuestAddress{0x32001000}, 0x11223344);
        {
            cd::DataImportRegistry d(r);
            reject([&] { d.admit_reference_projection(provider, projection()); },
                   cd::DataFaultReason::invalid_admission, d);
        }
        check(r.memory().load<std::uint32_t>(GuestAddress{0x32001000}) == 0x11223344,
              "Collision preserves external owned buffer");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        r.memory().map(GuestAddress{0x78037174}, 4, Permissions::read | Permissions::write);
        r.memory().store<std::uint32_t>(GuestAddress{0x78037174}, 0x55667788);
        {
            cd::DataImportRegistry d(r);
            reject([&] { d.admit_reference_projection(provider, projection()); },
                   cd::DataFaultReason::invalid_admission, d);
            check(d.record() && !d.record()->reference_projection_ready,
                  "Partial admission cannot become ready");
        }
        check(r.memory().load<std::uint32_t>(GuestAddress{0x78037174}) == 0x55667788,
              "Provider-global collision preserves external ownership");
        bool absent{};
        try {
            (void)r.memory().load<std::uint8_t>(GuestAddress{0x32001000});
        } catch (const MemoryFault &f) {
            absent = f.reason() == MemoryFaultReason::unmapped;
        }
        check(absent, "Partial admission releases only its acquired buffer mapping");
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        {
            cd::DataImportRegistry d(r);
            d.admit_reference_projection(provider, projection());
        }
        for (const auto address :
             std::array<GuestAddress, 2>{GuestAddress{0x32001000}, GuestAddress{0x78037174}}) {
            bool absent{};
            try {
                (void)r.memory().load<std::uint8_t>(address);
            } catch (const MemoryFault &f) {
                absent = f.reason() == MemoryFaultReason::unmapped;
            }
            check(absent, "Registry teardown releases its two owned maps");
        }
        check(r.memory().load<std::uint32_t>(GuestAddress{0x5bb518}) == 0xabcdef00 + 0x5bb518,
              "Registry teardown retains raw image IAT");
    }
    for (unsigned c = 0; c < 3; ++c) {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        cd::DataImportRegistry d(r);
        if (c == 0)
            reject([&] { (void)d.resolve_reference_load32(GuestAddress{0x5bb518}); },
                   cd::DataFaultReason::unresolved_data, d);
        else {
            d.admit_reference_projection(provider, projection());
            reject(
                [&] {
                    (void)d.resolve_reference_load32(GuestAddress{c == 1 ? 0x5bb508U : 0x5bb519U});
                },
                cd::DataFaultReason::unresolved_data, d);
        }
        reject([&] { (void)d.resolve_reference_load32(GuestAddress{0x5bb518}); },
               cd::DataFaultReason::unresolved_data, d);
    }
    for (unsigned c = 0; c < 4; ++c) {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        cd::DataImportRegistry d(r);
        d.admit_reference_projection(provider, projection());
        if (c == 0) {
            r.memory().protect(GuestAddress{0x5bb000}, Permissions::read | Permissions::write);
            r.memory().store<std::uint32_t>(GuestAddress{0x5bb518}, 0);
        }
        if (c == 1)
            r.memory().store<std::uint32_t>(GuestAddress{0x78037174}, 0);
        if (c == 2) {
            r.memory().protect(GuestAddress{0x32001000}, Permissions::read | Permissions::write);
            r.memory().store<std::uint8_t>(GuestAddress{0x32001000}, 0);
        }
        if (c == 3)
            r.memory().protect(GuestAddress{0x32001000}, Permissions::none);
        const auto reason =
            c == 3 ? cd::DataFaultReason::memory_fault : cd::DataFaultReason::changed_identity;
        reject([&] { (void)d.resolve_reference_load32(GuestAddress{0x5bb518}); }, reason, d);
        reject([&] { (void)d.resolve_reference_load32(GuestAddress{0x5bb518}); }, reason, d);
    }
    {
        auto r = Runtime::for_authored_fixture(fixture(), policy());
        cd::DataImportRegistry d(r);
        d.admit_reference_projection(provider, projection());
        reject([&] { d.admit_reference_projection(provider, projection()); },
               cd::DataFaultReason::invalid_admission, d);
    }
}
} // namespace
int main(int argc, char **argv) {
    try {
        check(argc == 4, "Data tests require private exact provider/game/original observation");
        provider = file(argv[1]);
        game = file(argv[2]);
        raw = file(argv[3]);
        check(m4::sha256(raw) == "40b786cd8ec580316141e883f3280c9a6e5c0f8053eb143a0a8f450f2e959ad9",
              "Exact frozen original observation required");
        tests();
        std::cout << checks
                  << " authored reference data ownership/admission checks passed; production "
                     "service false\n";
        return 0;
    } catch (const std::exception &e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
