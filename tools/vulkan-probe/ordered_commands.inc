// Shared by offscreen and windowed replay. Render pass is open on entry/exit.
for(const auto &op:scene.commands) {
    if(op[0]==1) { replayDraw(op[1]);continue; }
    if(op[0]==2) {
        std::array<VkClearAttachment,2> attachmentsToClear{};
        uint32_t clearAttachmentCount=0;
        if(op[1]&1U) {
            auto &a=attachmentsToClear[clearAttachmentCount++];a.aspectMask=VK_IMAGE_ASPECT_COLOR_BIT;a.colorAttachment=0;
            a.clearValue.color.float32[0]=static_cast<float>((op[6]>>16)&255)/255;
            a.clearValue.color.float32[1]=static_cast<float>((op[6]>>8)&255)/255;
            a.clearValue.color.float32[2]=static_cast<float>(op[6]&255)/255;
            a.clearValue.color.float32[3]=static_cast<float>((op[6]>>24)&255)/255;
        }
        if(op[1]&2U) {
            auto &a=attachmentsToClear[clearAttachmentCount++];a.aspectMask=VK_IMAGE_ASPECT_DEPTH_BIT;
            std::memcpy(&a.clearValue.depthStencil.depth,&op[7],4);
        }
        VkClearRect rect{{{static_cast<int32_t>(op[2]*scale),static_cast<int32_t>(op[3]*scale)},
                           {op[4]*scale,op[5]*scale}},0,1};
        vkCmdClearAttachments(command,clearAttachmentCount,attachmentsToClear.data(),1,&rect);continue;
    }
    if(colorMode!="rgba8")throw std::runtime_error("Surface copies currently require RGBA8 target");
    vkCmdEndRenderPass(command);
    transition(color.handle,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
               VK_ACCESS_COLOR_ATTACHMENT_READ_BIT|VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,VK_ACCESS_TRANSFER_WRITE_BIT,
               VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT);
    const auto source=textures[op[1]].handle;
    transition(source,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
               VK_ACCESS_SHADER_READ_BIT,VK_ACCESS_TRANSFER_READ_BIT,VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT);
    VkImageBlit region{};region.srcSubresource={VK_IMAGE_ASPECT_COLOR_BIT,0,0,1};region.dstSubresource=region.srcSubresource;
    region.srcOffsets[0]={static_cast<int32_t>(op[2]),static_cast<int32_t>(op[3]),0};
    region.srcOffsets[1]={static_cast<int32_t>(op[2]+op[6]),static_cast<int32_t>(op[3]+op[7]),1};
    region.dstOffsets[0]={static_cast<int32_t>(op[4]*scale),static_cast<int32_t>(op[5]*scale),0};
    region.dstOffsets[1]={static_cast<int32_t>((op[4]+op[6])*scale),static_cast<int32_t>((op[5]+op[7])*scale),1};
    vkCmdBlitImage(command,source,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,color.handle,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,1,&region,VK_FILTER_NEAREST);
    transition(source,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
               VK_ACCESS_TRANSFER_READ_BIT,VK_ACCESS_SHADER_READ_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT);
    transition(color.handle,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
               VK_ACCESS_TRANSFER_WRITE_BIT,VK_ACCESS_COLOR_ATTACHMENT_READ_BIT|VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
               VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT);
    const auto depthStages=VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT|VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT;
    const auto depthAccess=VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT|VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT;
    transition(depth.handle,VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,
               depthAccess,depthAccess,depthStages,depthStages,VK_IMAGE_ASPECT_DEPTH_BIT);
    vkCmdBeginRenderPass(command,&begin,VK_SUBPASS_CONTENTS_INLINE);
}
