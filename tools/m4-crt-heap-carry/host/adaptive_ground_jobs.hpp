#pragma once

#include "adaptive_ground_math.hpp"
#include "adaptive_ground_worker_environment.hpp"
#include <algorithm>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <deque>
#include <future>
#include <mutex>
#include <optional>
#include <thread>

namespace mw34::adaptive_ground {

inline unsigned bounded_worker_count(unsigned requested, unsigned hardware) {
    return std::max(1U, std::min(requested, std::max(1U, hardware)));
}

// A stale result is discarded, but its computation failure remains observable.
// Drain every handle even after a failure so no request outlives mesh storage.
inline void drain_completion(std::future<Result> &completion, std::exception_ptr &first_error) {
    if (!completion.valid())
        return;
    try {
        (void)completion.get();
    } catch (...) {
        if (!first_error)
            first_error = std::current_exception();
    }
}

// The only worker entry point is the pure numerical kernel. Requests own all
// nested inputs; neither Stage, guest memory nor renderer objects enter here.
class JobPool {
  public:
    struct Span {
        std::uint64_t frame{}, begin{}, end{};
        unsigned node{}, polygon{}, worker{};
        bool refined{};
    };

  private:
    struct Request {
        Input input;
        std::promise<Result> completion;
    };
    std::mutex mutex_;
    std::condition_variable available_;
    std::deque<Request> requests_;
    std::vector<std::jthread> workers_;
    bool closing_{};
    unsigned running_{};
    std::atomic<unsigned> active_{}, peak_{};
    std::atomic<std::uint64_t> submitted_{}, completed_{};
    bool record_spans_{}, span_overflow_{};
    std::vector<Span> spans_;

    void run(unsigned worker) {
        for (;;) {
            std::optional<Request> request;
            {
                std::unique_lock lock(mutex_);
                available_.wait(lock, [&] { return closing_ || !requests_.empty(); });
                if (requests_.empty())
                    return;
                request.emplace(std::move(requests_.front()));
                requests_.pop_front();
                ++running_;
            }
            const unsigned active = active_.fetch_add(1) + 1;
            unsigned peak = peak_.load();
            while (peak < active && !peak_.compare_exchange_weak(peak, active)) {
            }
            try {
                WorkerEnvironment environment;
                const auto frame = request->input.identity.camera.frame;
                const bool record = record_spans_ && (frame == 801 || frame == 849 ||
                                                      frame == 1801 || frame == 2101);
                const auto clock = [] {
                    return std::uint64_t(std::chrono::duration_cast<std::chrono::nanoseconds>(
                                             std::chrono::steady_clock::now().time_since_epoch())
                                             .count());
                };
                const auto begin = record ? clock() : 0;
                auto result = prepare(request->input);
                if (record) {
                    const Span span{frame,
                                    begin,
                                    clock(),
                                    request->input.identity.source_node,
                                    request->input.identity.polygon,
                                    worker,
                                    result.prepared && result.vertices.size() >
                                                           request->input.vertices.size() + 1};
                    std::lock_guard lock(mutex_);
                    if (spans_.size() < 4096)
                        spans_.push_back(span);
                    else
                        span_overflow_ = true;
                }
                request->completion.set_value(std::move(result));
            } catch (...) {
                request->completion.set_exception(std::current_exception());
            }
            --active_;
            ++completed_;
            {
                std::lock_guard lock(mutex_);
                --running_;
            }
        }
    }

    void close() noexcept {
        {
            std::lock_guard lock(mutex_);
            closing_ = true;
        }
        available_.notify_all();
        for (auto &worker : workers_)
            if (worker.joinable())
                worker.join();
    }

  public:
    // A mesh scope also retains at most capacity completed handles. At the
    // kernel's fixed capacities, this bounds input/result ownership below 32 MiB.
    static constexpr unsigned capacity = 64;

    explicit JobPool(unsigned workers, bool record_spans = false) : record_spans_(record_spans) {
        if (workers < 1 || workers > 4)
            throw std::runtime_error("Adaptive ground actual worker count must be 1 through 4");
        try {
            workers_.reserve(workers);
            for (unsigned index = 0; index < workers; ++index)
                workers_.emplace_back([this, index] { run(index); });
        } catch (...) {
            close();
            throw;
        }
    }
    JobPool(const JobPool &) = delete;
    JobPool &operator=(const JobPool &) = delete;
    ~JobPool() { close(); }

    std::optional<std::future<Result>> submit(Input input) {
        std::lock_guard lock(mutex_);
        if (closing_ || requests_.size() + running_ >= capacity)
            return {};
        Request request{std::move(input), {}};
        auto completion = request.completion.get_future();
        requests_.push_back(std::move(request));
        ++submitted_;
        available_.notify_one();
        return completion;
    }
    std::uint64_t submitted() const { return submitted_.load(); }
    std::uint64_t completed() const { return completed_.load(); }
    unsigned peak_active() const { return peak_.load(); }
    unsigned worker_count() const { return unsigned(workers_.size()); }
    std::vector<Span> spans() {
        std::lock_guard lock(mutex_);
        return spans_;
    }
    bool span_overflow() {
        std::lock_guard lock(mutex_);
        return span_overflow_;
    }
    // Main-thread diagnostics can read CPU time for these owned threads. The
    // handles are borrowed until pool destruction and never enter job inputs.
    std::vector<std::jthread::native_handle_type> native_threads() {
        std::vector<std::jthread::native_handle_type> handles;
        for (auto &worker : workers_)
            handles.push_back(worker.native_handle());
        return handles;
    }
};

} // namespace mw34::adaptive_ground
