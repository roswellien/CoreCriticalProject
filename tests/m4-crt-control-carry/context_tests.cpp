// Actual compiled callbacks only; no original game/vendor instructions execute.
#define main carry_observation_worker_main
#include "../../tools/m4-crt-control-carry/native_main.cpp"
#undef main

namespace {
unsigned checks{}, scenarios{};
std::vector<std::uint8_t> actual_image, actual_provider, actual_pack, actual_original;
void check(bool value, const char *why) {
    need(value, why);
    ++checks;
}
rt::Policy test_policy() {
    rt::Policy p;
    p.stack_low = {0x20001000};
    p.stack_bytes = 4096;
    return p;
}
struct Fixture {
    rt::Runtime runtime;
    State &state;
    control::Context context;
    control::SerialOwner owner;
    Fixture()
        : runtime(rt::Runtime::from_admitted_image(std::as_bytes(std::span{actual_image}),
                                                   test_policy())),
          state(seed_before_only(runtime, actual_original.data() + 32, 0)), context(runtime, state),
          owner(context) {
        mount_provider(runtime, actual_pack);
        register_all(runtime);
        ++scenarios;
    }
    void start() {
        control::HostScope host;
        runtime.call_direct({control::wrapper}, {control::outer_return});
        host.capture();
        check(!std::memcmp(host.before.bytes, host.after.bytes, 512) &&
                  !std::memcmp(host.env, host.env_after, 28),
              "Actual complete host restoration for control callback");
        check(runtime.calls().size() == 2 && runtime.calls()[0].completed &&
                  runtime.calls()[1].completed && context.count == 13,
              "Actual typed control route completes before numerical carry");
        check(state.x87.fxsave.cwd.flat == 0x27f &&
                  control::get<std::uint16_t>(
                      reinterpret_cast<const std::uint8_t *>(runtime.fx().data())) == 0x27f,
              "Actual source control output is carried in both views");
    }
    bool call(unsigned entry, carry::Native &record) {
        carry::observation = &record;
        bool rejected{};
        control::HostScope host;
        try {
            runtime.call_direct({entry}, {carry::broker});
        } catch (const rt::Fault &) {
            rejected = true;
        }
        carry::observation = nullptr;
        host.capture();
        check(!std::memcmp(host.before.bytes, host.after.bytes, 512) &&
                  !std::memcmp(host.env, host.env_after, 28),
              "Actual outer host restoration for successful and faulted carry callbacks");
        return rejected;
    }
    void denial(unsigned entry, const char *diagnostic = nullptr) {
        std::array<std::byte, 512> before{};
        std::memcpy(before.data(), runtime.fx().data(), 512);
        const auto state_mask =
            control::get<unsigned>(reinterpret_cast<const std::uint8_t *>(&state.x87) + 28);
        carry::Native record{};
        bool rejected{};
        carry::observation = &record;
        control::HostScope host;
        try {
            runtime.call_direct({entry}, {carry::broker});
        } catch (const rt::Fault &error) {
            rejected = true;
            if (diagnostic)
                check(std::string(error.what()).find(diagnostic) != std::string::npos,
                      "Exact intended capability-domain diagnosis");
        }
        carry::observation = nullptr;
        host.capture();
        check(!std::memcmp(host.before.bytes, host.after.bytes, 512) &&
                  !std::memcmp(host.env, host.env_after, 28),
              "Actual complete host restoration on required carry denial");
        check(rejected && runtime.poisoned() && !runtime.calls().back().completed,
              "Required carry fault poisons the real route rather than completing it");
        check(std::memcmp(before.data(), runtime.fx().data(), 512) == 0 &&
                  state_mask == control::get<unsigned>(
                                    reinterpret_cast<const std::uint8_t *>(&state.x87) + 28),
              "Temporary Request transport cannot reset either resident capability/whole FX view");
        const auto count = runtime.calls().size();
        carry::Native retry{};
        check(call(entry, retry) && runtime.calls().size() == count && context.count == 13 &&
                  !retry.state_seeded,
              "Poisoned carry runtime cannot execute another callback or fabricate an observation");
    }
};
void run_tests() {
    {
        Fixture fixture;
        fixture.start();
        auto &r = fixture.runtime;
        auto &s = fixture.state;
        std::array<std::byte, 3504> initial{};
        std::memcpy(initial.data(), &s, 3504);
        std::array<std::byte, 512> previous_fx{};
        std::memcpy(previous_fx.data(), r.fx().data(), 512);
        for (auto entry : carry::entries) {
            carry::Native record{};
            check(!fixture.call(entry, record) && record.state_seeded &&
                      record.common.host_restored,
                  "Actual compiled selected root succeeds under observed control result");
            check(s.x87.fxsave.cwd.flat == 0x27f &&
                      control::get<std::uint16_t>(
                          reinterpret_cast<const std::uint8_t *>(r.fx().data())) == 0x27f,
                  "Every compiled callback retains actual PC53 control result without reseeding");
            check(control::get<unsigned>(reinterpret_cast<const std::uint8_t *>(&s.x87) + 28) ==
                          0x2ffff &&
                      control::get<unsigned>(reinterpret_cast<const std::uint8_t *>(r.fx().data()) +
                                             28) == 0x2ffff,
                  "Every callback retains complete measured capability metadata");
            check(std::memcmp(record.state_after.data(), &s, 3504) == 0,
                  "Recorded full State is the persistent Runtime object after each callback");
            check(std::memcmp(initial.data() + 3280, reinterpret_cast<const std::byte *>(&s) + 3280,
                              224) == 0 &&
                      s.addr.fs_base.dword == r.fs_base().value,
                  "All hidden State tail and guest FS storage persist through all numerical "
                  "operations");
            std::memcpy(previous_fx.data(), r.fx().data(), 512);
        }
        check(r.calls().size() == 28 && !r.poisoned() && r.translation_count() == 27 &&
                  fixture.context.count == 13,
              "Complete actual27-phase routing extent and one persistent control Context");
    }
    // Both integer adapter families use a temporary validator Request; every
    // changed resident capability field must be rejected before any guest body.
    for (unsigned entry : {0x410910U, 0x43aec0U})
        for (unsigned location = 0; location < 3; ++location)
            for (unsigned value : {0U, 0x2fffeU, 0xffffffffU}) {
                Fixture fixture;
                fixture.start();
                if (location != 1)
                    std::memcpy(fixture.runtime.fx().data() + 28, &value, 4);
                if (location != 0)
                    std::memcpy(reinterpret_cast<std::byte *>(&fixture.state.x87) + 28, &value, 4);
                fixture.denial(entry, "Observed carry FX capability mask changed");
            }
    {
        Fixture fixture;
        fixture.start();
        fixture.state.addr.fs_base.dword += 4;
        fixture.denial(0x4133c0);
    }
    {
        Fixture fixture;
        fixture.start();
        fixture.runtime.fx()[0] = std::byte{0x7e};
        fixture.denial(0x4133c0);
    }
    {
        Fixture fixture;
        fixture.start();
        fixture.state.x87.fxsave.swd.flat |= 0x8000;
        fixture.runtime.fx()[3] |= std::byte{0x80};
        fixture.denial(0x4133c0);
    }
}
} // namespace
int main(int argc, char **argv) {
    try {
        need(argc == 5, "Carry controls: exact-image exact-provider exact-pack exact-original");
        actual_image = read(argv[1], 2384384);
        actual_provider = read(argv[2], 266293);
        actual_pack = read(argv[3], 106716);
        actual_original = read(argv[4], 60000000);
        need(digest(actual_image) == m4::admitted_image_hash &&
                 digest(actual_provider) == original::provider_sha &&
                 digest(actual_pack) == original::pack_sha &&
                 digest(actual_original) == carry::original_raw_sha,
             "Exact frozen carry control input association");
        run_tests();
        std::cout
            << checks << " compiled carry checks across " << scenarios
            << " scenarios passed; original/vendor instructions not executed; full CRT false\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
