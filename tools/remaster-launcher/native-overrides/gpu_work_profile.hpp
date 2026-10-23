#pragma once
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <stdexcept>
#include <string>
#include <utility>

namespace mw34::diagnostic {
// Opt-in attribution only. Separate query pools follow the renderer's existing
// scene/present fences. Reading results never introduces a GPU completion wait.
class GpuWorkProfile {
    struct LastError {
        DWORD value = ::GetLastError();
        ~LastError() { ::SetLastError(value); }
    };
    FILE* output{};
    VkDevice device{};
    VkPhysicalDevice gpu{};
    PFN_vkCreateQueryPool createPool{};
    PFN_vkDestroyQueryPool destroyPool{};
    PFN_vkCmdResetQueryPool resetPool{};
    PFN_vkCmdWriteTimestamp writeStamp{};
    PFN_vkGetQueryPoolResults getResults{};
    PFN_vkGetPhysicalDeviceMemoryProperties2KHR memoryProperties{};
    unsigned validBits{};
    double period{};
    std::uint64_t frame{}, present{}, scene{};
    struct Span { const char* label{}; bool ended{}; };
    struct Bank {
        VkQueryPool pool{};
        std::array<Span, 16> spans{};
        unsigned count{};
        bool pending{};
        std::uint64_t frame{}, present{}, scene{};
    };
    std::array<Bank, 2> banks{};

    static void require(VkResult result) {
        if (result != VK_SUCCESS)
            throw std::runtime_error("GPU attribution query failed: " + std::to_string(int(result)));
    }
  public:
    GpuWorkProfile() {
        LastError error;
        if (const char* path = std::getenv("MW34_GPU_WORK_LOG"); path && *path) {
            output = std::fopen(path, "wx");
            if (!output) throw std::runtime_error("Cannot create fresh MW34_GPU_WORK_LOG");
            std::setvbuf(output, nullptr, _IOFBF, 65536);
            std::fputs("event,label,world_frame,present_frame,scene,a,b,c,d\n", output);
        }
    }
    ~GpuWorkProfile() { LastError error; if (output) std::fclose(output); }
    GpuWorkProfile(const GpuWorkProfile&) = delete;
    GpuWorkProfile& operator=(const GpuWorkProfile&) = delete;
    bool enabled() const { return output != nullptr; }
    LARGE_INTEGER clock() const {
        LastError error;
        LARGE_INTEGER value{};
        if (output) ::QueryPerformanceCounter(&value);
        return value;
    }
    void elapsed(const char* label, LARGE_INTEGER begin) {
        if (!output) return;
        LastError error;
        LARGE_INTEGER end{}, frequency{};
        ::QueryPerformanceCounter(&end); ::QueryPerformanceFrequency(&frequency);
        event("cpu_ns", label, std::uint64_t((end.QuadPart-begin.QuadPart) *
              (1000000000.0/frequency.QuadPart)));
    }
    void context(std::uint64_t f, std::uint64_t p, std::uint64_t s) {
        frame = f; present = p; scene = s;
    }
    void event(const char* type, const char* label, std::uint64_t a = 0,
               std::uint64_t b = 0, std::uint64_t c = 0, std::uint64_t d = 0) {
        if (!output) return;
        LastError error;
        if (std::fprintf(output, "%s,%s,%llu,%llu,%llu,%llu,%llu,%llu,%llu\n",
                         type, label, frame, present, scene, a, b, c, d) < 0)
            throw std::runtime_error("GPU attribution log write failed");
    }
    template<class Fn> VkResult call(const char* label, Fn&& fn) {
        if (!output) return fn();
        LARGE_INTEGER begin{}, end{}, frequency{};
        const DWORD before = ::GetLastError();
        ::QueryPerformanceCounter(&begin);
        ::SetLastError(before);
        const VkResult result = fn();
        const DWORD after = ::GetLastError();
        ::QueryPerformanceCounter(&end); ::QueryPerformanceFrequency(&frequency);
        event("cpu_ns", label, std::uint64_t((end.QuadPart - begin.QuadPart) *
              (1000000000.0 / frequency.QuadPart)), std::uint64_t(std::int64_t(result)));
        ::SetLastError(after);
        return result;
    }
    void initialize(VkDevice d, VkPhysicalDevice g, PFN_vkGetDeviceProcAddr get,
                    unsigned bits, double nanoseconds,
                    PFN_vkGetPhysicalDeviceMemoryProperties2KHR memory) {
        LastError error;
        if (!output) return;
        device = d; gpu = g; validBits = bits; period = nanoseconds; memoryProperties = memory;
        if (!bits || bits > 64 || !(nanoseconds > 0))
            throw std::runtime_error("GPU attribution requires supported queue timestamps");
#define MW34_PROFILE_LOAD(member, name) \
        member = reinterpret_cast<PFN_##name>(get(device, #name)); \
        if (!member) throw std::runtime_error("GPU attribution missing " #name)
        MW34_PROFILE_LOAD(createPool, vkCreateQueryPool);
        MW34_PROFILE_LOAD(destroyPool, vkDestroyQueryPool);
        MW34_PROFILE_LOAD(resetPool, vkCmdResetQueryPool);
        MW34_PROFILE_LOAD(writeStamp, vkCmdWriteTimestamp);
        MW34_PROFILE_LOAD(getResults, vkGetQueryPoolResults);
#undef MW34_PROFILE_LOAD
        for (auto& bank : banks) {
            VkQueryPoolCreateInfo info{VK_STRUCTURE_TYPE_QUERY_POOL_CREATE_INFO};
            info.queryType = VK_QUERY_TYPE_TIMESTAMP; info.queryCount = 32;
            require(createPool(device, &info, nullptr, &bank.pool));
        }
        event("metadata", "timestamp_bits_period_ps", bits, std::uint64_t(period * 1000));
        event("metadata", "memory_budget_supported", memoryProperties != nullptr);
    }
    void begin(unsigned slot, VkCommandBuffer command, const char* label) {
        LastError error;
        if (!output) return;
        auto& bank = banks.at(slot);
        if (bank.pending) throw std::runtime_error("GPU query pool reused before existing fence completion");
        bank.count = 0; bank.frame = frame; bank.present = present; bank.scene = scene;
        resetPool(command, bank.pool, 0, 32);
        start(slot, command, label);
    }
    unsigned start(unsigned slot, VkCommandBuffer command, const char* label) {
        LastError error;
        if (!output) return 0;
        auto& bank = banks.at(slot);
        if (bank.count == bank.spans.size()) throw std::runtime_error("GPU attribution span capacity exceeded");
        const unsigned index = bank.count++;
        bank.spans[index] = {label, false};
        // Whole submission: TOP->BOTTOM. Nested regions: BOTTOM->BOTTOM,
        // measuring incremental completion intervals without adding barriers.
        // GPU stages can overlap; these intervals are not isolated busy times.
        writeStamp(command, index ? VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT :
                   VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, bank.pool, index * 2);
        return index;
    }
    void end(unsigned slot, VkCommandBuffer command, unsigned index) {
        LastError error;
        if (!output) return;
        auto& bank = banks.at(slot);
        if (index >= bank.count || bank.spans[index].ended)
            throw std::runtime_error("Invalid GPU attribution span end");
        writeStamp(command, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, bank.pool, index * 2 + 1);
        bank.spans[index].ended = true;
    }
    void finish(unsigned slot, VkCommandBuffer command) {
        LastError error;
        if (!output) return;
        end(slot, command, 0);
        banks.at(slot).pending = true;
    }
    void collect(unsigned slot) {
        LastError error;
        if (!output) return;
        auto& bank = banks.at(slot);
        if (!bank.pending) return;
        struct Value { std::uint64_t ticks{}, available{}; };
        std::array<Value, 32> values{};
        // The caller has ALREADY completed the existing fence/device wait.
        // No WAIT_BIT, no polling loop, no additional synchronization.
        require(getResults(device, bank.pool, 0, bank.count * 2, sizeof(values), values.data(),
                           sizeof(Value), VK_QUERY_RESULT_64_BIT | VK_QUERY_RESULT_WITH_AVAILABILITY_BIT));
        const auto old = std::array{frame, present, scene};
        context(bank.frame, bank.present, bank.scene);
        const std::uint64_t mask = validBits == 64 ? ~0ULL : (1ULL << validBits) - 1;
        for (unsigned i = 0; i < bank.count; ++i) {
            if (!bank.spans[i].ended || !values[i*2].available || !values[i*2+1].available)
                throw std::runtime_error("GPU timestamp unavailable after completed fence");
            const auto ticks = (values[i*2+1].ticks - values[i*2].ticks) & mask;
            event("gpu_ns", bank.spans[i].label, std::uint64_t(ticks * period));
        }
        context(old[0], old[1], old[2]); bank.pending = false;
    }
    void sampleMemory(std::uint64_t p) {
        if (!output || !memoryProperties || p % 60) return;
        LastError error;
        VkPhysicalDeviceMemoryBudgetPropertiesEXT budget{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MEMORY_BUDGET_PROPERTIES_EXT};
        VkPhysicalDeviceMemoryProperties2 properties{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_MEMORY_PROPERTIES_2};
        properties.pNext = &budget; memoryProperties(gpu, &properties);
        const auto old = present; present = p;
        for (unsigned i = 0; i < properties.memoryProperties.memoryHeapCount; ++i)
            event("memory_bytes", "heap_usage_budget", i, budget.heapUsage[i], budget.heapBudget[i],
                  properties.memoryProperties.memoryHeaps[i].flags);
        present = old;
    }
    void shutdown() {
        LastError error;
        if (!output || !device) return;
        collect(0); collect(1);
        for (auto& bank : banks) if (bank.pool) {
            destroyPool(device, bank.pool, nullptr); bank.pool = {};
        }
        device = {};
    }
};
} // namespace mw34::diagnostic
