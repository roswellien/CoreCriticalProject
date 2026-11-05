#pragma once

#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <deque>
#include <exception>
#include <functional>
#include <future>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string>
#include <thread>
#include <type_traits>
#include <utility>

namespace mw34::render_thread {

// Nonzero while the render thread is inside a call that may send window messages to the game
// thread, which owns the windows: swapchain creation or resizing, exclusive full screen and the
// present. A message sent to another thread's window waits until that thread handles it, so the
// game thread handles sent messages while it waits, but only then; a window procedure never runs
// at an unrelated wait.
inline std::atomic<int> window_message_calls{0};
struct SendsWindowMessages {
    SendsWindowMessages() { window_message_calls.fetch_add(1); }
    ~SendsWindowMessages() { window_message_calls.fetch_sub(1); }
    SendsWindowMessages(const SendsWindowMessages &) = delete;
    SendsWindowMessages &operator=(const SendsWindowMessages &) = delete;
};

// Runs host graphics commands in submission order on one worker thread, or at
// once on the caller's thread in inline mode. Only the game thread submits.
// The worker owns every Vulkan object while threaded, so read-backs run on it
// through drain(). A worker exception is kept and re-raised at the game thread's
// next enqueue, drain or end_frame, naming the command that failed.
class RenderQueue {
  public:
    using Clock = std::chrono::steady_clock;
    static constexpr std::chrono::milliseconds default_timeout{20000};
    static constexpr std::chrono::milliseconds slice{2};

    // Threaded mode starts the worker here; a failure to start throws, and the
    // caller then builds an inline queue instead.
    explicit RenderQueue(bool threaded, std::chrono::milliseconds timeout = default_timeout)
        : timeout_(timeout) {
        if (threaded)
            worker_ = std::thread([this] { work(); });
    }
    RenderQueue(const RenderQueue &) = delete;
    RenderQueue &operator=(const RenderQueue &) = delete;
    // A worker that cannot be stopped is still using this object, so neither
    // joining nor detaching is safe; the failure terminates visibly instead.
    ~RenderQueue() {
        try {
            stop();
        } catch (const std::exception &e) {
            std::fprintf(stderr, "render thread stuck at exit: %s\n", e.what());
            std::abort();
        }
    }

    bool threaded() const { return worker_.joinable(); }

    // Called between wait slices on the game thread, outside the queue's lock.
    void set_between_waits(std::function<void()> fn) { between_waits_ = std::move(fn); }

    template <class F> void enqueue(const char *label, F &&fn) {
        if (!threaded()) {
            fn();
            return;
        }
        std::lock_guard lock(mutex_);
        raise_error();
        push(label, std::forward<F>(fn));
    }

    // Waits until every earlier command has run, then runs fn on the worker and
    // returns its result.
    template <class F> auto drain(const char *label, F &&fn) -> std::invoke_result_t<F &> {
        using Result = std::invoke_result_t<F &>;
        if (!threaded())
            return fn();
        std::packaged_task<Result()> call(std::forward<F>(fn));
        auto result = call.get_future();
        std::uint64_t ticket;
        {
            std::lock_guard lock(mutex_);
            raise_error();
            ticket = push(label, std::move(call));
        }
        wait(label, ticket);
        return result.get();
    }

    // Marks a frame boundary. Blocks while the previous frame's commands are
    // still running, so the game thread runs at most one frame ahead.
    void end_frame() {
        if (!threaded())
            return;
        std::uint64_t previous;
        {
            std::lock_guard lock(mutex_);
            previous = frame_mark_;
            frame_mark_ = submitted_;
        }
        wait("end of frame", previous);
    }

    // Runs everything queued, then joins the worker; later commands run inline.
    // A stuck worker throws "Render thread stuck in <label>" and stays running.
    void stop() {
        if (!threaded())
            return;
        std::uint64_t last;
        {
            std::lock_guard lock(mutex_);
            last = submitted_;
        }
        wait("stop", last, false);
        {
            std::lock_guard lock(mutex_);
            stopping_ = true;
        }
        work_.notify_one();
        worker_.join();
    }

    // Game-thread wait time and count since the last call, for the frame log.
    struct WaitStats {
        double ms{};
        unsigned count{};
    };
    WaitStats take_wait_stats() { return std::exchange(waits_, WaitStats{}); }

  private:
    struct Task {
        virtual ~Task() = default;
        virtual void run() = 0;
    };
    template <class F> struct TaskOf final : Task {
        F fn;
        explicit TaskOf(F &&f) : fn(std::move(f)) {}
        void run() override { fn(); }
    };
    struct Command {
        const char *label;
        std::unique_ptr<Task> task;
    };

    template <class F> std::uint64_t push(const char *label, F &&fn) {
        using Fn = std::decay_t<F>;
        queue_.push_back({label, std::make_unique<TaskOf<Fn>>(Fn(std::forward<F>(fn)))});
        work_.notify_one();
        return ++submitted_;
    }

    // Callers hold the lock. The first error is reported once; the worker then
    // runs later commands again.
    void raise_error() {
        if (!error_)
            return;
        auto error = std::exchange(error_, nullptr);
        const std::string where = std::exchange(error_label_, nullptr);
        try {
            std::rethrow_exception(error);
        } catch (const std::exception &e) {
            throw std::runtime_error("Render thread failed in " + where + ": " + e.what());
        } catch (...) {
            throw std::runtime_error("Render thread failed in " + where);
        }
    }

    // Waits on the game thread until the command numbered ticket has finished.
    void wait(const char *label, std::uint64_t ticket, bool report_error = true) {
        std::unique_lock lock(mutex_);
        if (completed_ >= ticket) {
            if (report_error)
                raise_error();
            return;
        }
        const auto start = Clock::now();
        while (completed_ < ticket) {
            if (Clock::now() - start >= timeout_) {
                waits_.ms +=
                    std::chrono::duration<double, std::milli>(Clock::now() - start).count();
                ++waits_.count;
                throw std::runtime_error(std::string("Render thread stuck in ") +
                                         (running_ ? running_ : label));
            }
            done_.wait_for(lock, slice);
            if (between_waits_ && completed_ < ticket) {
                lock.unlock();
                between_waits_();
                lock.lock();
            }
        }
        waits_.ms += std::chrono::duration<double, std::milli>(Clock::now() - start).count();
        ++waits_.count;
        if (report_error)
            raise_error();
    }

    // After a failure the worker skips commands until the error is reported.
    void work() {
        std::unique_lock lock(mutex_);
        for (;;) {
            work_.wait(lock, [&] { return stopping_ || !queue_.empty(); });
            if (queue_.empty())
                return;
            Command command = std::move(queue_.front());
            queue_.pop_front();
            const bool skip = static_cast<bool>(error_);
            running_ = command.label;
            lock.unlock();
            std::exception_ptr failed;
            if (!skip) {
                try {
                    command.task->run();
                } catch (...) {
                    failed = std::current_exception();
                }
            }
            // Scenes and their vertex data are freed here, off the game thread.
            command.task.reset();
            lock.lock();
            if (failed && !error_) {
                error_ = failed;
                error_label_ = command.label;
            }
            running_ = nullptr;
            ++completed_;
            done_.notify_all();
        }
    }

    std::chrono::milliseconds timeout_;
    std::function<void()> between_waits_;
    std::mutex mutex_;
    std::condition_variable work_, done_;
    std::deque<Command> queue_;
    std::uint64_t submitted_{}, completed_{}, frame_mark_{};
    const char *running_{};
    std::exception_ptr error_;
    const char *error_label_{};
    bool stopping_{};
    WaitStats waits_;
    std::thread worker_;
};

} // namespace mw34::render_thread
