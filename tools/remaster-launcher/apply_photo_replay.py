"""Install Photo Mode (F11), camera controls (C), screenshots (F9), and rewind (Shift+F11)."""
from pathlib import Path
import argparse
import shutil
from apply_capture_readback import apply as apply_capture_readback


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if text.count(old) != 1:
        raise RuntimeError(f"Expected exactly one occurrence of {label} (found {text.count(old)})")
    return text.replace(old, new, 1)


def apply(source: Path):
    overrides_dir = Path(__file__).parent / "native-overrides"
    for name in ("photo_replay_math.hpp", "photo_replay_stage.inc"):
        shutil.copyfile(overrides_dir / name, source / name)

    # 1. Patch mfc_stage.hpp
    mfc_path = source / "mfc_stage.hpp"
    mfc_text = mfc_path.read_text(encoding="utf-8")

    mfc_text = replace_once(
        mfc_text,
        '#include "turret_aim_math.hpp"',
        '#include "turret_aim_math.hpp"\n#include "photo_replay_math.hpp"',
        "turret_aim_math.hpp include",
    )
    mfc_text = replace_once(
        mfc_text,
        ' #include "turret_aim_stage.inc"',
        ' #include "turret_aim_stage.inc"\n #include "photo_replay_stage.inc"',
        "turret_aim_stage.inc include",
    )
    mfc_text = replace_once(
        mfc_text,
        " void*remaster_body(State*s,unsigned target,void*p,Body body){\n  return turret_aim_body(s,target,p,[&]{return remaster_body_inner(s,target,p,body);});\n }",
        " void*remaster_body(State*s,unsigned target,void*p,Body body){\n  return photo_replay_body(s,target,p,[&]{return turret_aim_body(s,target,p,[&]{return remaster_body_inner(s,target,p,body);});});\n }",
        "remaster_body wrapper",
    )
    old_gds_v1 = 'if(n=="GetDeviceState"){const unsigned z=arg(1),a=arg(2);if(z>4096||!writable(a,z))deny("GetDeviceState buffer outside the memory contract",a);std::vector<unsigned char>b(z);const HRESULT hr=dv->GetDeviceState(z,b.data());if(SUCCEEDED(hr)){if(photo_replay_consume_input())std::fill(b.begin(),b.end(),0);for(unsigned i=0;i<z;++i)runtime.memory().store<unsigned char>({a+i},b[i]);}return done(unsigned(hr),3);}'
    if old_gds_v1 in mfc_text:
        mfc_text = mfc_text.replace(
            old_gds_v1,
            'if(n=="GetDeviceState"){const unsigned z=arg(1),a=arg(2);if(z>4096||!writable(a,z))deny("GetDeviceState buffer outside the memory contract",a);std::vector<unsigned char>b(z);const HRESULT hr=dv->GetDeviceState(z,b.data());if(SUCCEEDED(hr)){photo_replay_filter_device_state(z,b.data());for(unsigned i=0;i<z;++i)runtime.memory().store<unsigned char>({a+i},b[i]);}return done(unsigned(hr),3);}',
            1,
        )
    else:
        mfc_text = replace_once(
            mfc_text,
            'if(n=="GetDeviceState"){const unsigned z=arg(1),a=arg(2);if(z>4096||!writable(a,z))deny("GetDeviceState buffer outside the memory contract",a);std::vector<unsigned char>b(z);const HRESULT hr=dv->GetDeviceState(z,b.data());if(SUCCEEDED(hr))for(unsigned i=0;i<z;++i)runtime.memory().store<unsigned char>({a+i},b[i]);return done(unsigned(hr),3);}',
            'if(n=="GetDeviceState"){const unsigned z=arg(1),a=arg(2);if(z>4096||!writable(a,z))deny("GetDeviceState buffer outside the memory contract",a);std::vector<unsigned char>b(z);const HRESULT hr=dv->GetDeviceState(z,b.data());if(SUCCEEDED(hr)){photo_replay_filter_device_state(z,b.data());for(unsigned i=0;i<z;++i)runtime.memory().store<unsigned char>({a+i},b[i]);}return done(unsigned(hr),3);}',
            "DirectInput GetDeviceState hook",
        )

    old_gdd_v1 = 'if(SUCCEEDED(hr)){if(photo_replay_consume_input())cnt=0;if(a)for(DWORD k=0;k<cnt;++k){b[k].dwTimeStamp=host.guest_tick_of(b[k].dwTimeStamp);for(unsigned i=0;i<16;++i)runtime.memory().store<unsigned char>({a+16*k+i},reinterpret_cast<const unsigned char*>(&b[k])[i]);}store(pn,cnt);}return done(unsigned(hr),5);}'
    if old_gdd_v1 in mfc_text:
        mfc_text = mfc_text.replace(
            old_gdd_v1,
            'if(SUCCEEDED(hr)){photo_replay_filter_device_data(b.data(),cnt);if(a)for(DWORD k=0;k<cnt;++k){b[k].dwTimeStamp=host.guest_tick_of(b[k].dwTimeStamp);for(unsigned i=0;i<16;++i)runtime.memory().store<unsigned char>({a+16*k+i},reinterpret_cast<const unsigned char*>(&b[k])[i]);}store(pn,cnt);}return done(unsigned(hr),5);}',
            1,
        )
    else:
        mfc_text = replace_once(
            mfc_text,
            'if(SUCCEEDED(hr)){if(a)for(DWORD k=0;k<cnt;++k){b[k].dwTimeStamp=host.guest_tick_of(b[k].dwTimeStamp);for(unsigned i=0;i<16;++i)runtime.memory().store<unsigned char>({a+16*k+i},reinterpret_cast<const unsigned char*>(&b[k])[i]);}store(pn,cnt);}return done(unsigned(hr),5);}',
            'if(SUCCEEDED(hr)){photo_replay_filter_device_data(b.data(),cnt);if(a)for(DWORD k=0;k<cnt;++k){b[k].dwTimeStamp=host.guest_tick_of(b[k].dwTimeStamp);for(unsigned i=0;i<16;++i)runtime.memory().store<unsigned char>({a+16*k+i},reinterpret_cast<const unsigned char*>(&b[k])[i]);}store(pn,cnt);}return done(unsigned(hr),5);}',
            "DirectInput GetDeviceData hook",
        )
    mfc_path.write_text(mfc_text, encoding="utf-8")

    # 2. Patch vk_scene.hpp (add capture_fullres_rgb)
    vk_path = source / "vk_scene.hpp"
    vk_text = vk_path.read_text(encoding="utf-8")
    capture_method = """        std::fclose(out);
    }
    void capture_fullres_rgb(std::vector<std::uint8_t> &out_rgb, unsigned &out_w, unsigned &out_h) {
        HostFpEnvironment fp;
        finish_world();
        settle();
        out_w = rw;
        out_h = rh;
        if (!rw || !rh || !colorImage.image) { out_rgb.clear(); return; }
        const VkDeviceSize bytes = VkDeviceSize(rw) * rh * (rgba ? 4 : 2);
        ensure(readback, std::max<VkDeviceSize>(bytes, VkDeviceSize(width) * height * 4), VK_BUFFER_USAGE_TRANSFER_DST_BIT);
        check(f.vkResetCommandPool(device, commandPool, 0), "reset command pool");
        VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
        bi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        check(f.vkBeginCommandBuffer(cmd, &bi), "begin capture");
        if (in_attachment_layout) {
            barrier(colorImage.image, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_TRANSFER_READ_BIT,
                    VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
            barrier(depthImage.image, VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT, VK_ACCESS_TRANSFER_READ_BIT,
                    VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_DEPTH_BIT);
        }
        VkBufferImageCopy c{};
        c.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1}; c.imageExtent = {rw, rh, 1};
        f.vkCmdCopyImageToBuffer(cmd, colorImage.image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, readback.buffer, 1, &c);
        VkMemoryBarrier hb{VK_STRUCTURE_TYPE_MEMORY_BARRIER};
        hb.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT; hb.dstAccessMask = VK_ACCESS_HOST_READ_BIT;
        f.vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_HOST_BIT, 0, 1, &hb, 0, nullptr, 0, nullptr);
        check(f.vkEndCommandBuffer(cmd), "end capture");
        check(f.vkResetFences(device, 1, &fence), "reset fence");
        VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};
        si.commandBufferCount = 1; si.pCommandBuffers = &cmd;
        check(f.vkQueueSubmit(queue, 1, &si, fence), "submit capture");
        check(f.vkWaitForFences(device, 1, &fence, VK_TRUE, 10000000000ULL), "wait capture");
        in_attachment_layout = false;
        const auto *src = static_cast<const unsigned char *>(readback.mapped);
        out_rgb.resize(size_t(rw) * rh * 3);
        for (unsigned y = 0; y < rh; ++y) {
            for (unsigned x = 0; x < rw; ++x) {
                std::uint8_t *o = &out_rgb[(size_t(y) * rw + x) * 3];
                if (rgba) { const unsigned char *p = src + (size_t(y) * rw + x) * 4; o[0] = p[0]; o[1] = p[1]; o[2] = p[2]; }
                else { const unsigned p = src[(size_t(y) * rw + x) * 2] | (src[(size_t(y) * rw + x) * 2 + 1] << 8); o[0] = ((p >> 11) & 31) * 255 / 31; o[1] = ((p >> 5) & 63) * 255 / 63; o[2] = (p & 31) * 255 / 31; }
            }
        }
    }"""
    vk_text = replace_once(
        vk_text,
        "        std::fclose(out);\n    }",
        capture_method,
        "dump_fullres closing in vk_scene.hpp",
    )
    vk_path.write_text(vk_text, encoding="utf-8")

    # 3. Patch vdd.inc (clean screenshot/video capture before overlay + GPU hotkey legend overlay)
    vdd_path = source / "vdd.inc"
    vdd_text = vdd_path.read_text(encoding="utf-8")
    vdd_text = replace_once(
        vdd_text,
        "if(present_direct){host.presenter->finish_world();if(host.presenter->overlay.on)overlay_gpu(w,h);",
        "if(present_direct){host.presenter->finish_world();photo_replay_on_present(w,h,true,px,v.pitch);if(host.presenter->overlay.on)overlay_gpu(w,h);",
        "present_direct hook in vdd.inc",
    )
    vdd_text = replace_once(
        vdd_text,
        "if(!present_direct)shown=host.presenter->present(host.display.window,px.data(),w,h,v.pitch,wide_on()&&!frontend_on()&&wide_world_frame==host.frames);",
        "if(!present_direct){photo_replay_on_present(w,h,false,px,v.pitch);shown=host.presenter->present(host.display.window,px.data(),w,h,v.pitch,wide_on()&&!frontend_on()&&wide_world_frame==host.frames);}",
        "non-present_direct hook in vdd.inc",
    )
    vdd_path.write_text(vdd_text, encoding="utf-8")

    # 4. Patch gpu_hud.inc (suppress 2D HUD flush when H is toggled)
    hud_path = source / "gpu_hud.inc"
    hud_text = hud_path.read_text(encoding="utf-8")
    hud_text = replace_once(
        hud_text,
        "void hud_flush(){if(hud_sc.draws.empty())return;",
        "void hud_flush(){if(hud_sc.draws.empty())return;if(photo_replay_hide_hud()){hud_begin(*vsurface(host.res_rt));return;}",
        "hud_flush hook in gpu_hud.inc",
    )
    hud_path.write_text(hud_text, encoding="utf-8")

    # 5. Patch d3d_provider.inc (suppress translucent HUD panel D3D draw when H is toggled)
    d3d_path = source / "d3d_provider.inc"
    d3d_text = d3d_path.read_text(encoding="utf-8")
    d3d_text = replace_once(
        d3d_text,
        "if(!override_suppress_draw())dev->commands.push_back(std::move(c));",
        "if(!override_suppress_draw()&&!photo_replay_suppress_d3d_draw(c.hud_role))dev->commands.push_back(std::move(c));",
        "DrawPrimitive suppression hook in d3d_provider.inc",
    )
    d3d_path.write_text(d3d_text, encoding="utf-8")

    # 6. Patch guest_memory_cached.cpp (enable MEM_WRITE_WATCH for hardware dirty page tracking)
    mem_path = source / "guest_memory_cached.cpp"
    mem_text = mem_path.read_text(encoding="utf-8")
    mem_text = replace_once(
        mem_text,
        "void *p = ::VirtualAlloc(nullptr, static_cast<SIZE_T>(reservation), MEM_RESERVE, PAGE_NOACCESS);",
        "void *p = ::VirtualAlloc(nullptr, static_cast<SIZE_T>(reservation), MEM_RESERVE | MEM_WRITE_WATCH, PAGE_NOACCESS);\n    if (!p) p = ::VirtualAlloc(nullptr, static_cast<SIZE_T>(reservation), MEM_RESERVE, PAGE_NOACCESS);",
        "VirtualAlloc MEM_WRITE_WATCH in guest_memory_cached.cpp",
    )
    mem_path.write_text(mem_text, encoding="utf-8")
    apply_capture_readback(source)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host_source", type=Path)
    apply(parser.parse_args().host_source)
