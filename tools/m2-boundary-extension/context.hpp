#pragma once
#include "memory/guest_memory.hpp"
#include "protocol.hpp"
#include <algorithm>
#include <map>
#include <remill/Arch/X86/Runtime/State.h>
#include <string>
namespace m2_boundary_extension {
using NativeBlock = void *(*)(State *, std::uint32_t, void *);
struct Route {
    NativeBlock original{}, replacement{};
    bool continuation{};
    std::uint32_t cleanup{};
};
struct Frame {
    std::uint32_t target, return_pc, esp, cleanup;
};
struct Context {
    mw34::GuestMemory memory;

  private:
    std::map<std::uint32_t, Route> routes;
    bool frozen{};
    using TimerReader = std::uint32_t (*)(const void *);
    TimerReader timer_reader{};
    const void *timer_cookie{};
    std::string timer_identity;

  public:
    std::vector<Frame> frames;
    std::uint32_t calls{}, returns{}, resume{}, budget{32}, outer_esp{};
    bool final_return{};
    std::uint32_t replacement_calls{};
    std::uint32_t provider_calls{}, bridge_calls{}, provider_return{};
    void timer_provider(std::string identity, TimerReader reader, const void *cookie) {
        if (frozen || timer_reader || !reader ||
            (identity != "deterministic-uint32" && identity != "WINMM.timeGetTime"))
            throw std::runtime_error("Frozen/conflicting/unknown timer provider");
        timer_identity = std::move(identity);
        timer_reader = reader;
        timer_cookie = cookie;
    }
    std::uint32_t read_timer() {
        if (!frozen || !timer_reader) throw std::runtime_error("Timer provider not admitted");
        ++provider_calls;
        provider_return = timer_reader(timer_cookie);
        return provider_return;
    }
    void add(std::uint32_t pc, Route route) {
        constexpr std::uint32_t admitted[] = {
            code_base,         code_base + 0xf,   code_base + 0x20,  code_base + 0x2d,
            code_base + 0x200, code_base + 0x300, code_base + 0x400, code_base + 0x500};
        auto found = std::find(std::begin(admitted), std::end(admitted), pc);
        if (frozen || found == std::end(admitted) ||
            route.continuation != (found < std::begin(admitted) + 4) ||
            route.cleanup != (pc == code_base + 0x200 ? 4U : 0U) || !route.original ||
            !routes.emplace(pc, route).second)
            throw std::runtime_error("Frozen/duplicate/invalid route registration");
    }
    void select(std::uint32_t pc, NativeBlock fn) {
        if (frozen || !fn)
            throw std::runtime_error("Frozen/invalid replacement selection");
        auto found = routes.find(pc);
        if (found == routes.end() || found->second.replacement)
            throw std::runtime_error("Unknown/conflicting replacement");
        found->second.replacement = fn;
    }
    void freeze(const std::string &image) {
        if (frozen || image != fixture_hash || routes.size() != 8 || !timer_reader)
            throw std::runtime_error("Wrong image or incomplete/frozen registry");
        frozen = true;
    }
    void *route(State *state, std::uint32_t target, bool original = false) {
        if (!frozen)
            throw std::runtime_error("Unfrozen registry execution");
        if (state->gpr.rip.dword != target)
            throw std::runtime_error(
                "Guest PC/route mismatch pc=" + std::to_string(state->gpr.rip.dword) +
                " target=" + std::to_string(target));
        auto found = routes.find(target);
        if (found == routes.end())
            throw std::runtime_error(
                "Unknown guest route pc=" + std::to_string(state->gpr.rip.dword) +
                " target=" + std::to_string(target));
        if (!budget)
            throw std::runtime_error("Bounded route budget exceeded");
        --budget;
        bool replacement = !original && found->second.replacement;
        if (replacement)
            ++replacement_calls;
        auto fn = replacement ? found->second.replacement : found->second.original;
        return fn(state, target, this);
    }
    void *call(State *state, std::uint32_t target) {
        auto found = routes.find(target);
        if (found == routes.end() || found->second.continuation)
            throw std::runtime_error(
                "Unknown/non-call guest target pc=" + std::to_string(state->gpr.rip.dword) +
                " target=" + std::to_string(target));
        auto esp = state->gpr.rsp.dword;
        auto ret = memory.load<std::uint32_t>({esp});
        auto continuation = routes.find(ret);
        auto expected_return = target == code_base + 0x200   ? code_base + 0xf
                               : target == code_base + 0x300 ? code_base + 0x20
                                                             : code_base + 0x2d;
        if (continuation == routes.end() || !continuation->second.continuation ||
            ret != expected_return)
            throw std::runtime_error("Unknown guest return pc=" + std::to_string(ret) +
                                     " target=" + std::to_string(target));
        frames.push_back({target, ret, esp, found->second.cleanup});
        ++calls;
        auto *token = route(state, target);
        if (!frames.empty() && frames.back().target == target)
            throw std::runtime_error("Missing guest return");
        return token;
    }
    void *returned(State *state, std::uint32_t target) {
        if (state->gpr.rip.dword != target)
            throw std::runtime_error("Returned PC mismatch");
        ++returns;
        if (frames.empty()) {
            if (target != sentinel || final_return ||
                std::uint64_t{outer_esp} + 4 != state->gpr.rsp.dword)
                throw std::runtime_error("Unknown/duplicate/malformed outer return");
            final_return = true;
            return this;
        }
        auto frame = frames.back();
        if (target != frame.return_pc ||
            std::uint64_t{frame.esp} + 4 + frame.cleanup != state->gpr.rsp.dword)
            throw std::runtime_error("Return target/stack cleanup mismatch");
        frames.pop_back();
        resume = target;
        return this;
    }
    void *continuation(State *state, std::uint32_t target) {
        if (target != resume)
            throw std::runtime_error("Unadmitted continuation");
        resume = 0;
        auto found = routes.find(target);
        if (found == routes.end() || !found->second.continuation)
            throw std::runtime_error("Unknown continuation");
        return route(state, target);
    }
};
} // namespace m2_boundary_extension
