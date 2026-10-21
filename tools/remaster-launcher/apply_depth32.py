"""Upgrade main Vulkan depth attachments while retaining the guest D16 ABI."""
from pathlib import Path
import shutil


def apply(host):
    host = Path(host)
    path = host / 'vk_scene.hpp'
    text = path.read_text(encoding='utf-8')
    if '#include "depth_transfer.hpp"' in text:
        shutil.copy2(Path(__file__).parent / 'native-overrides/depth_transfer.hpp', host / 'depth_transfer.hpp')
        return

    def edit(old, new, count=1):
        nonlocal text
        if text.count(old) != count:
            raise ValueError(f'Unexpected Vulkan depth source anchor ({text.count(old)}): {old[:90]}')
        text = text.replace(old, new)

    text = '#include "depth_transfer.hpp"\n' + text
    edit('const VkDeviceSize colorBytes = pixels * (rgba ? 4 : 2), depthBytes = pixels * 2;',
         'const VkDeviceSize colorBytes = pixels * (rgba ? 4 : 2), depthOffset = mw34::depth::offset(size_t(colorBytes)), depthBytes = pixels * sizeof(float);')
    edit('ensure(upload, colorBytes + depthBytes,', 'ensure(upload, depthOffset + depthBytes,')
    edit('ensure(readback, colorBytes + depthBytes,', 'ensure(readback, depthOffset + depthBytes,')
    edit('if (upload_in) std::memcpy(up + colorBytes, s.depth.data(), depthBytes);',
         'if (upload_in) mw34::depth::upload(up + depthOffset, s.depth.data(), size_t(pixels));')
    edit('copy_in_scaled(colorBytes);', 'copy_in_scaled(depthOffset);')
    edit('copy_out_scaled(colorBytes);', 'copy_out_scaled(mw34::depth::offset(size_t(colorBytes)));', 2)
    edit('const VkDeviceSize pixels = VkDeviceSize(width) * height, colorBytes = pixels * (rgba ? 4 : 2), depthBytes = pixels * 2;',
         'const VkDeviceSize pixels = VkDeviceSize(width) * height, colorBytes = pixels * (rgba ? 4 : 2);')
    edit('std::memcpy(s.depth.data(), rd + colorBytes, depthBytes);',
         'mw34::depth::readback(s.depth.data(), rd + mw34::depth::offset(size_t(colorBytes)), size_t(pixels));')
    edit('at[1].format = VK_FORMAT_D16_UNORM;', 'at[1].format = VK_FORMAT_D32_SFLOAT;')
    edit('f.vkGetPhysicalDeviceFormatProperties(gpu, VK_FORMAT_D16_UNORM, &dp);',
         'f.vkGetPhysicalDeviceFormatProperties(gpu, VK_FORMAT_D32_SFLOAT, &dp);')
    for target in ['depthLo', 'depthImage']:
        dims = 'w, h' if target == 'depthLo' else 'rw, rh'
        edit(f'image({target}.image, {target}.memory, {target}.view, {dims}, VK_FORMAT_D16_UNORM,',
             f'image({target}.image, {target}.memory, {target}.view, {dims}, VK_FORMAT_D32_SFLOAT,')
    # Shadow maps have their own capability policy and are deliberately untouched.
    edit('f.vkGetPhysicalDeviceMemoryProperties(gpu, &memory);', '''f.vkGetPhysicalDeviceMemoryProperties(gpu, &memory);
        VkFormatProperties depthProperties{};
        f.vkGetPhysicalDeviceFormatProperties(gpu, VK_FORMAT_D32_SFLOAT, &depthProperties);
        const VkFormatFeatureFlags depthNeed = VK_FORMAT_FEATURE_DEPTH_STENCIL_ATTACHMENT_BIT | VK_FORMAT_FEATURE_BLIT_SRC_BIT | VK_FORMAT_FEATURE_BLIT_DST_BIT;
        if ((depthProperties.optimalTilingFeatures & depthNeed) != depthNeed)
            throw std::runtime_error("GPU does not support required 32-bit floating-point depth attachments and blits");''')
    # The argument is the aligned staging offset, not the colour byte count.
    for name in ['copy_in_scaled', 'copy_out_scaled']:
        start = text.index('void ' + name + '(')
        end = text.index('\n    }', start) + len('\n    }')
        text = text[:start] + text[start:end].replace('colorBytes', 'depthOffset') + text[end:]
    shutil.copy2(Path(__file__).parent / 'native-overrides/depth_transfer.hpp', host / 'depth_transfer.hpp')
    path.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    apply(parser.parse_args().host)
