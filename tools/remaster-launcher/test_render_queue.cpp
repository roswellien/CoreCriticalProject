#include "../m4-crt-heap-carry/host/render_thread.hpp"
#include <atomic>
#include <chrono>
#include <future>
#include <iostream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

namespace {
using mw34::render_thread::RenderQueue;
using namespace std::chrono_literals;

unsigned checks = 0;
void check(bool value, const char *what) {
    ++checks;
    if (!value)
        throw std::runtime_error(std::string("Render queue check failed: ") + what);
}

// Returns the message of the exception fn throws, or an empty string.
template <class F> std::string error_from(F &&fn) {
    try {
        fn();
    } catch (const std::exception &error) {
        return error.what();
    }
    return {};
}

void check_order(bool threaded) {
    RenderQueue queue(threaded);
    std::vector<int> seen;
    for (int i = 0; i < 200; ++i)
        queue.enqueue("append", [&seen, i] { seen.push_back(i); });
    const auto count = queue.drain("count", [&] { return seen.size(); });
    check(count == 200, "drain sees every earlier command");
    for (int i = 0; i < 200; ++i)
        check(seen[static_cast<std::size_t>(i)] == i, "commands run in order");
}

void check_drain_waits(bool threaded) {
    RenderQueue queue(threaded);
    bool finished = false;
    queue.enqueue("slow", [&] {
        std::this_thread::sleep_for(30ms);
        finished = true;
    });
    check(queue.drain("read", [&] { return finished; }), "drain runs after earlier commands");
    unsigned pumped = 0;
    queue.set_between_waits([&] { ++pumped; });
    queue.enqueue("slow", [] { std::this_thread::sleep_for(30ms); });
    queue.drain("read", [] {});
    check(!threaded || pumped > 0, "long waits call between_waits");
    const auto waits = queue.take_wait_stats();
    check(!threaded || (waits.count > 0 && waits.ms > 0), "waits are counted");
    check(queue.take_wait_stats().count == 0, "wait stats reset when taken");
}

void check_frame_limit() {
    RenderQueue queue(true);
    std::promise<void> gate;
    auto opened = gate.get_future().share();
    std::atomic<bool> frame_done{false};
    queue.enqueue("frame 1", [opened, &frame_done] {
        opened.wait();
        frame_done = true;
    });
    queue.end_frame(); // frame 1 may still run while frame 2 is built
    check(!frame_done, "the first end_frame does not wait");
    std::thread opener([&] {
        std::this_thread::sleep_for(50ms);
        gate.set_value();
    });
    const auto start = RenderQueue::Clock::now();
    queue.end_frame(); // frame 2 cannot end until frame 1 has run
    const auto waited = RenderQueue::Clock::now() - start;
    opener.join();
    check(frame_done, "end_frame waits for the previous frame");
    check(waited >= 30ms, "end_frame blocks the producer");
}

void check_errors(bool threaded) {
    RenderQueue queue(threaded);
    if (!threaded) {
        const auto message = error_from(
            [&] { queue.enqueue("boom", [] { throw std::runtime_error("bad scene"); }); });
        check(message == "bad scene", "inline errors reach the caller at once");
        return;
    }
    bool skipped_ran = false;
    queue.enqueue("boom", [] { throw std::runtime_error("bad scene"); });
    // The failure may already be stored when "after" is queued, so either call may report it.
    const auto message = error_from([&] {
        queue.enqueue("after", [&] { skipped_ran = true; });
        queue.drain("read", [] {});
    });
    check(message == "Render thread failed in boom: bad scene", "worker errors name the command");
    check(!skipped_ran, "commands after a failure are skipped");
    queue.enqueue("fill", [] { throw std::runtime_error("bad fill"); });
    const auto later = error_from([&] { queue.drain("settle", [] {}); });
    check(later == "Render thread failed in fill: bad fill", "each failure is reported once");
    check(queue.drain("recover", [] { return 7; }) == 7, "the queue runs again after reporting");
}

void check_timeout() {
    RenderQueue queue(true, 100ms);
    std::promise<void> gate;
    auto opened = gate.get_future().share();
    queue.enqueue("slow scene", [opened] { opened.wait(); });
    const auto message = error_from([&] { queue.drain("read", [] {}); });
    check(message == "Render thread stuck in slow scene", "the timeout names the stuck command");
    gate.set_value();
    queue.stop();
}

void check_timeout_counts_progress() {
    RenderQueue queue(true, 100ms);
    // Six 40 ms commands take longer than the timeout in total, but each finishes well inside it.
    for (int i = 0; i < 6; ++i)
        queue.enqueue("shader build", [] { std::this_thread::sleep_for(40ms); });
    const auto message = error_from([&] { queue.drain("read", [] {}); });
    check(message.empty(), "steady progress is not called stuck");
    queue.stop();
}

void check_stop(bool threaded) {
    RenderQueue queue(threaded);
    std::atomic<int> ran{0};
    for (int i = 0; i < 20; ++i)
        queue.enqueue("tick", [&] {
            std::this_thread::sleep_for(1ms);
            ++ran;
        });
    queue.stop();
    check(ran == 20, "stop runs queued commands first");
    check(!queue.threaded(), "stop joins the worker");
    queue.enqueue("late", [&] { ++ran; });
    check(ran == 21, "commands after stop run inline");
}

void run_render_queue_checks() {
    for (const bool threaded : {false, true}) {
        check_order(threaded);
        check_drain_waits(threaded);
        check_errors(threaded);
        check_stop(threaded);
    }
    check_frame_limit();
    check_timeout();
    check_timeout_counts_progress();
    std::cout << "render queue checks=" << checks << " failures=0\n";
}
} // namespace

// Report a failed check as an ordinary test failure. An uncaught exception
// aborts, and a Debug build then waits on an error dialog instead of exiting.
int main() {
    try {
        run_render_queue_checks();
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
