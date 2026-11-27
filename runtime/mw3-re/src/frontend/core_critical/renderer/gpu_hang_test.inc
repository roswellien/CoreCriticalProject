// Included inside Renderer. Test only (#521, MW3_TEST_DEVICE_LOST): one
// compute dispatch that never ends, submitted before a present, so the GPU
// timeout resets the driver and the lost-device report runs for real. Nothing
// here is made unless the switch is set; teardown destroys it with the device.
std::optional<std::chrono::steady_clock::time_point> hang_gpu_at_;
VkDescriptorSetLayout hangSetLayout{};
VkPipelineLayout hangLayout{};
VkPipeline hangPipeline{};
VkDescriptorPool hangPool{};
VkCommandPool hangCommandPool{};
Buffer hangSink;

void hang_gpu_if_due() {
  if (!hang_gpu_at_ || std::chrono::steady_clock::now() < *hang_gpu_at_)
    return;
  hang_gpu_at_.reset();
  MW3_LOG(I, "mw3: test switch MW3_TEST_DEVICE_LOST: submitting a dispatch that never ends\n");
  std::fflush(stdout);
  const VkDescriptorSetLayoutBinding binding{0, VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, 1,
                                             VK_SHADER_STAGE_COMPUTE_BIT, nullptr};
  VkDescriptorSetLayoutCreateInfo sl{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
  sl.bindingCount = 1;
  sl.pBindings = &binding;
  check(f.vkCreateDescriptorSetLayout(device, &sl, nullptr, &hangSetLayout), "hang set layout");
  const VkPushConstantRange push{VK_SHADER_STAGE_COMPUTE_BIT, 0, sizeof(std::uint32_t)};
  VkPipelineLayoutCreateInfo pl{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
  pl.setLayoutCount = 1;
  pl.pSetLayouts = &hangSetLayout;
  pl.pushConstantRangeCount = 1;
  pl.pPushConstantRanges = &push;
  check(f.vkCreatePipelineLayout(device, &pl, nullptr, &hangLayout), "hang pipeline layout");
  VkShaderModuleCreateInfo sm{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};
  sm.codeSize = sizeof(test_gpu_hang_comp_spv);
  sm.pCode = test_gpu_hang_comp_spv;
  VkShaderModule module{};
  check(f.vkCreateShaderModule(device, &sm, nullptr, &module), "hang shader module");
  VkComputePipelineCreateInfo cp{VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO};
  cp.stage.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
  cp.stage.stage = VK_SHADER_STAGE_COMPUTE_BIT;
  cp.stage.module = module;
  cp.stage.pName = "main";
  cp.layout = hangLayout;
  const auto created = f.vkCreateComputePipelines(device, VK_NULL_HANDLE, 1, &cp, nullptr, &hangPipeline);
  f.vkDestroyShaderModule(device, module, nullptr);
  check(created, "hang compute pipeline");
  ensure_device_buffer(hangSink, 256, VK_BUFFER_USAGE_STORAGE_BUFFER_BIT);
  const VkDescriptorPoolSize size{VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, 1};
  VkDescriptorPoolCreateInfo pi{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
  pi.maxSets = 1;
  pi.poolSizeCount = 1;
  pi.pPoolSizes = &size;
  check(f.vkCreateDescriptorPool(device, &pi, nullptr, &hangPool), "hang descriptor pool");
  VkDescriptorSetAllocateInfo ai{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
  ai.descriptorPool = hangPool;
  ai.descriptorSetCount = 1;
  ai.pSetLayouts = &hangSetLayout;
  VkDescriptorSet set{};
  check(f.vkAllocateDescriptorSets(device, &ai, &set), "hang descriptor set");
  const VkDescriptorBufferInfo sink{hangSink.buffer, 0, VK_WHOLE_SIZE};
  VkWriteDescriptorSet write{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};
  write.dstSet = set;
  write.descriptorCount = 1;
  write.descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER;
  write.pBufferInfo = &sink;
  f.vkUpdateDescriptorSets(device, 1, &write, 0, nullptr);
  VkCommandPoolCreateInfo cpi{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
  cpi.queueFamilyIndex = family;
  check(f.vkCreateCommandPool(device, &cpi, nullptr, &hangCommandPool), "hang command pool");
  VkCommandBufferAllocateInfo cai{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
  cai.commandPool = hangCommandPool;
  cai.commandBufferCount = 1;
  VkCommandBuffer cmd{};
  check(f.vkAllocateCommandBuffers(device, &cai, &cmd), "hang command buffer");
  VkCommandBufferBeginInfo begin{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
  check(f.vkBeginCommandBuffer(cmd, &begin), "hang begin");
  f.vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_COMPUTE, hangPipeline);
  f.vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_COMPUTE, hangLayout, 0, 1, &set, 0, nullptr);
  const std::uint32_t limit = 0xFFFFFFFFu;
  f.vkCmdPushConstants(cmd, hangLayout, VK_SHADER_STAGE_COMPUTE_BIT, 0, sizeof limit, &limit);
  f.vkCmdDispatch(cmd, 1, 1, 1);
  check(f.vkEndCommandBuffer(cmd), "hang end");
  VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};
  si.commandBufferCount = 1;
  si.pCommandBuffers = &cmd;
  check(f.vkQueueSubmit(queue, 1, &si, VK_NULL_HANDLE), "submit hang");
}

void destroy_gpu_hang() {
  if (hangCommandPool)
    f.vkDestroyCommandPool(device, hangCommandPool, nullptr);
  if (hangPool)
    f.vkDestroyDescriptorPool(device, hangPool, nullptr);
  if (hangPipeline)
    f.vkDestroyPipeline(device, hangPipeline, nullptr);
  if (hangLayout)
    f.vkDestroyPipelineLayout(device, hangLayout, nullptr);
  if (hangSetLayout)
    f.vkDestroyDescriptorSetLayout(device, hangSetLayout, nullptr);
  if (hangSink.buffer)
    f.vkDestroyBuffer(device, hangSink.buffer, nullptr);
  if (hangSink.memory)
    release_memory(device, hangSink.memory, nullptr);
  hangCommandPool = {};
  hangPool = {};
  hangPipeline = {};
  hangLayout = {};
  hangSetLayout = {};
  hangSink = {};
}
