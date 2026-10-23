#define VK_NO_PROTOTYPES
#include <vulkan/vulkan_core.h>
#include <windows.h>
#include "../native-overrides/gpu_work_profile.hpp"
#include <cstring>
#include <iostream>
#include <vector>

namespace {
unsigned pools{}, destroyed{}, resets{}, reads{}, checks{};
bool ready{};
std::vector<VkPipelineStageFlagBits> stages;
void require(bool value) {
    ++checks;
    if (!value) throw std::runtime_error("GPU attribution fixture failed");
}
VKAPI_ATTR VkResult VKAPI_CALL create(VkDevice, const VkQueryPoolCreateInfo* info,
                                     const VkAllocationCallbacks*, VkQueryPool* pool) {
    require(info->queryType == VK_QUERY_TYPE_TIMESTAMP && info->queryCount == 32);
    *pool = reinterpret_cast<VkQueryPool>(std::uintptr_t(++pools)); SetLastError(900); return VK_SUCCESS;
}
VKAPI_ATTR void VKAPI_CALL destroy(VkDevice, VkQueryPool, const VkAllocationCallbacks*) { ++destroyed; SetLastError(901); }
VKAPI_ATTR void VKAPI_CALL reset(VkCommandBuffer, VkQueryPool, unsigned first, unsigned count) {
    require(first == 0 && count == 32); ++resets; SetLastError(902);
}
VKAPI_ATTR void VKAPI_CALL stamp(VkCommandBuffer, VkPipelineStageFlagBits stage, VkQueryPool, unsigned index) {
    require(index < 32); stages.push_back(stage); SetLastError(903);
}
VKAPI_ATTR VkResult VKAPI_CALL results(VkDevice, VkQueryPool, unsigned first, unsigned count,
                                      std::size_t size, void* data, VkDeviceSize stride, VkQueryResultFlags flags) {
    ++reads; SetLastError(904);
    require(first == 0 && count > 0 && count <= 32 && size >= count * stride);
    require(flags == (VK_QUERY_RESULT_64_BIT | VK_QUERY_RESULT_WITH_AVAILABILITY_BIT));
    require(stride == 16);
    if (!ready) return VK_NOT_READY;
    for (unsigned i=0;i<count;++i) {
        const std::uint64_t value[2]{i%2 ? 5ULL : 250ULL, 1};
        std::memcpy(static_cast<unsigned char*>(data)+i*stride,value,sizeof(value));
    }
    return VK_SUCCESS;
}
VKAPI_ATTR PFN_vkVoidFunction VKAPI_CALL get(VkDevice, const char* name) {
    if (!std::strcmp(name,"vkCreateQueryPool")) return reinterpret_cast<PFN_vkVoidFunction>(create);
    if (!std::strcmp(name,"vkDestroyQueryPool")) return reinterpret_cast<PFN_vkVoidFunction>(destroy);
    if (!std::strcmp(name,"vkCmdResetQueryPool")) return reinterpret_cast<PFN_vkVoidFunction>(reset);
    if (!std::strcmp(name,"vkCmdWriteTimestamp")) return reinterpret_cast<PFN_vkVoidFunction>(stamp);
    if (!std::strcmp(name,"vkGetQueryPoolResults")) return reinterpret_cast<PFN_vkVoidFunction>(results);
    return nullptr;
}
template<class Fn> void rejected(Fn fn) {
    bool failed=false; try { fn(); } catch(const std::runtime_error&) { failed=true; }
    require(failed);
}
}
int main(int argc,char** argv) {
    try {
        require(argc==2);
        _putenv_s("MW34_GPU_WORK_LOG","");
        {
            mw34::diagnostic::GpuWorkProfile disabled;
            require(!disabled.enabled());
            disabled.begin(0,{},"disabled");disabled.end(0,{},0);disabled.finish(0,{});
            disabled.collect(0); disabled.shutdown();
            require(pools==0 && reads==0 && stages.empty());
        }
        _putenv_s("MW34_GPU_WORK_LOG",argv[1]);
        {
            mw34::diagnostic::GpuWorkProfile profile;
            require(profile.enabled());
            auto device=reinterpret_cast<VkDevice>(std::uintptr_t(1));
            auto command=reinterpret_cast<VkCommandBuffer>(std::uintptr_t(2));
            profile.context(1200,1201,9000);
            SetLastError(701);
            profile.initialize(device,{},get,8,2,nullptr);
            require(GetLastError()==701);
            require(pools==2);
            SetLastError(123);
            require(profile.call("mock_wait",[]{SetLastError(456);return VK_SUCCESS;})==VK_SUCCESS);
            require(GetLastError()==456);
            SetLastError(789);
            profile.begin(0,command,"scene");require(GetLastError()==789);
            const auto shadow=profile.start(0,command,"shadow");
            profile.end(0,command,shadow);require(GetLastError()==789);
            rejected([&]{profile.end(0,command,shadow);});
            profile.finish(0,command);require(GetLastError()==789);
            rejected([&]{profile.begin(0,command,"premature_reuse");});
            // Present resources have their own independent pending query bank.
            profile.begin(1,command,"present");profile.finish(1,command);
            rejected([&]{profile.collect(0);});require(GetLastError()==789);
            require(reads==1);
            ready=true;
            profile.collect(0);profile.collect(1);require(GetLastError()==789);
            require(reads==3 && resets==2);
            profile.collect(0);require(reads==3);
            profile.begin(0,command,"next_scene");profile.finish(0,command);
            profile.shutdown();require(GetLastError()==789);
            require(destroyed==2 && reads==4);
            profile.shutdown();require(destroyed==2);
        }
        _putenv_s("MW34_GPU_WORK_LOG","");
        std::cout << "GPU attribution checks=" << checks << " failures=0\n";
    } catch(const std::exception& error) {
        std::cerr << error.what() << '\n';return 1;
    }
}
