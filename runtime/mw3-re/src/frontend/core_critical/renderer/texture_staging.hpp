#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <memory>

#include "platform/rgb565.hpp"
#include "texture_source.hpp"

namespace mw34::texture_staging {
// One texel of the renderer's 16-bit inputs (format 0 RGB565, 1 ARGB1555,
// 2 ARGB4444) widened to RGBA8 with the shared rounding in platform/rgb565.hpp.
// Convert in CPU-cached memory, then copy contiguous blocks to write-combined
// Vulkan staging memory. No reads of mapped upload memory are required.
inline std::uint32_t expand(std::uint16_t p, unsigned format) {
  namespace rgb565 = ::platform::rgb565;
  if (format == 0)
    return rgb565::to_rgba8(p);
  const unsigned value = p;
  unsigned red, green, blue, alpha;
  if (format == 1) {
    red = rgb565::widen_channel((value >> 10) & 31, 31);
    green = rgb565::widen_channel((value >> 5) & 31, 31);
    blue = rgb565::widen_channel(value & 31, 31);
    alpha = (value & 0x8000) ? 255 : 0;
  } else {
    red = rgb565::widen_channel((value >> 8) & 15, 15);
    green = rgb565::widen_channel((value >> 4) & 15, 15);
    blue = rgb565::widen_channel(value & 15, 15);
    alpha = rgb565::widen_channel(value >> 12, 15);
  }
  return red | green << 8 | blue << 16 | alpha << 24;
}
// The three tables take 768 KB, so they are built once on the heap: a copy of
// that size on the stack could overflow the render worker's thread.
inline const std::array<std::uint32_t,65536>& table(unsigned format) {
    using Tables = std::array<std::array<std::uint32_t, 65536>, 3>;
    static const std::unique_ptr<const Tables> tables = [] {
        auto values = std::make_unique<Tables>();
        for (unsigned staging_format = 0; staging_format < 3; ++staging_format)
            for (unsigned value = 0; value < 65536; ++value)
                (*values)[staging_format][value] = expand(std::uint16_t(value), staging_format);
        return std::unique_ptr<const Tables>(std::move(values));
    }();
    return tables->at(format);
}
inline void copy(unsigned char* destination,const std::uint16_t* source,std::size_t count,unsigned format) {
    const auto& lookup=table(format);
    std::array<std::uint32_t,4096> chunk;
    while(count){
        const auto n=std::min(count,chunk.size());
        for(std::size_t i=0;i<n;++i)chunk[i]=lookup[source[i]];
        std::memcpy(destination,chunk.data(),n*sizeof(chunk[0]));
        source+=n;destination+=n*sizeof(chunk[0]);count-=n;
    }
}

// 16-bit storage (#518). Every texture reaches the renderer as RGBA8, but most
// hold 16-bit data widened on the way: the game decodes its bank textures from
// RGB565, ARGB1555 or ARGB4444 by repeating each channel's bits
// (gamez/zvideo/zvid_ddd3d.cpp, texture_rgba), and the frontend widens pack
// replacement images and prepared skins from RGB565 as `c * 255 / max`
// rounded down (platform/rgb565.hpp, called by frame_renderer.cpp's
// image_pixels). Dropping each channel's low bits undoes either widening
// exactly, so such a texture can go to the card at 2 bytes per texel and
// sample the same 16-bit values it came from. The
// frontend says which format each texture's texels came from (TextureRef's
// pack16); nothing reads the texels to work it out.
enum class Pack16 : std::uint8_t { none, r5g6b5, a1r5g5b5, b4g4r4a4 };

// Bit flags for masks of 16-bit formats (which ones a device can use).
constexpr unsigned pack16_bit(Pack16 format) { return 1u << unsigned(format); }
constexpr unsigned kAllPack16 =
    pack16_bit(Pack16::r5g6b5) | pack16_bit(Pack16::a1r5g5b5) | pack16_bit(Pack16::b4g4r4a4);

// The 16-bit format the game decoded an upload from, given the format code of
// its upload key (native_texture_identity.hpp's SurfaceKey: 1 RGB565,
// 2 ARGB1555, 3 ARGB4444, as zvid's create_texture and reload_texture set it
// around the upload); none for 0 (no key) or anything else.
inline Pack16 pack16_for_upload_format(std::uint32_t format) {
  if (format == 1)
    return Pack16::r5g6b5;
  if (format == 2)
    return Pack16::a1r5g5b5;
  if (format == 3)
    return Pack16::b4g4r4a4;
  return Pack16::none;
}

// One RGBA8 texel in a 16-bit Vulkan layout, keeping each channel's top bits.
inline std::uint16_t pack16_texel(std::uint32_t texel, Pack16 format) {
  const unsigned red = texel & 0xff;
  const unsigned green = (texel >> 8) & 0xff;
  const unsigned blue = (texel >> 16) & 0xff;
  const unsigned alpha = texel >> 24;
  if (format == Pack16::r5g6b5) // VK_FORMAT_R5G6B5_UNORM_PACK16
    return std::uint16_t((red >> 3) << 11 | (green >> 2) << 5 | blue >> 3);
  if (format == Pack16::a1r5g5b5) // VK_FORMAT_A1R5G5B5_UNORM_PACK16
    return std::uint16_t((alpha >> 7) << 15 | (red >> 3) << 10 | (green >> 3) << 5 | blue >> 3);
  // VK_FORMAT_B4G4R4A4_UNORM_PACK16
  return std::uint16_t((blue >> 4) << 12 | (green >> 4) << 8 | (red >> 4) << 4 | alpha >> 4);
}

// Writes an RGBA8 texture of 16-bit data into staging at 16 bits: the inverse
// of both widenings above. Like copy(), it converts in CPU-cached memory and
// copies whole chunks, since staging memory is write-combined.
// native_texture_identity.hpp's canonical_upload_key keeps its own 16-bit
// packing for hashes; this one is only for the card.
inline void pack16(unsigned char *destination, const std::uint32_t *rgba, std::size_t count,
                   Pack16 format) {
  std::array<std::uint16_t, 4096> chunk;
  while (count) {
    const auto chunk_count = std::min(count, chunk.size());
    for (std::size_t index = 0; index < chunk_count; ++index)
      chunk[index] = pack16_texel(rgba[index], format);
    std::memcpy(destination, chunk.data(), chunk_count * sizeof(chunk[0]));
    rgba += chunk_count;
    destination += chunk_count * sizeof(chunk[0]);
    count -= chunk_count;
  }
}

// Staging bytes for one texture: 2 or 4 per texel, rounded up to 4 so every
// texture's staging offset stays 4-byte aligned for vkCmdCopyBufferToImage.
inline std::uint64_t staged_bytes(unsigned width, unsigned height, Pack16 pack) {
  const std::uint64_t texel_bytes = pack == Pack16::none ? 4 : 2;
  const std::uint64_t bytes = std::uint64_t(width) * height * texel_bytes;
  return (bytes + 3) / 4 * 4;
}

// Stages an RGBA8 texture as RGBA8 or at 16 bits.
inline void stage_rgba8(unsigned char *destination, const std::uint32_t *rgba,
                        std::size_t count, Pack16 pack) {
  if (pack == Pack16::none)
    std::memcpy(destination, rgba, count * sizeof(*rgba));
  else
    pack16(destination, rgba, count, pack);
}

// Which kinds of texture may be stored at 16 bits: an allow-list, so normal
// maps, canvases and any future data texture stay RGBA8 unless named here.
inline bool may_pack16(mw34::vkscene::TextureSource source) {
  return source == mw34::vkscene::TextureSource::guest ||
         source == mw34::vkscene::TextureSource::prepared_skin;
}

// How an upload picks its storage. At a mission preload the content is new,
// so the format follows it and the image is remade when that differs, except
// that an RGBA8 image is narrowed only when that strands no memory (below).
// During play, content can change every frame, so an image never narrows: it
// keeps its format while new content arrives in that same format, and
// otherwise becomes RGBA8.
enum class Pack16Rule : std::uint8_t { from_content, keep_or_widen };
struct Pack16Choice {
  Pack16 pack{Pack16::none};
  bool recreate{};
};
// Called only for an upload that needs pixels and has them. `content` is the
// 16-bit format the texels hold exactly (none when unknown, or when the source
// may not be narrowed); `allowed` is the formats the device can use now.
// `narrowing_is_free` matters only at a preload: whether remaking the current
// image strands no memory, because it is remade anyway (a new size) or
// destroying it gives its memory back to the card. Preload images share
// memory blocks that go back only with their last image, so narrowing one
// that shares a block would keep its old slice allocated beside the new
// 16-bit copy; it stays RGBA8 instead, which holds any content exactly.
inline Pack16Choice choose_pack16(Pack16Rule rule, bool has_image, Pack16 current,
                                  Pack16 content, unsigned allowed, bool narrowing_is_free) {
  const bool usable = content != Pack16::none && (allowed & pack16_bit(content)) != 0;
  const Pack16 wanted = usable ? content : Pack16::none;
  if (!has_image)
    return {wanted, false};
  if (wanted == current)
    return {current, false};
  const bool narrowing = current == Pack16::none;
  if (rule == Pack16Rule::from_content) {
    if (narrowing && !narrowing_is_free)
      return {current, false};
    return {wanted, true};
  }
  // During play an RGBA8 image stays RGBA8, and a 16-bit one widens.
  if (narrowing)
    return {current, false};
  return {Pack16::none, true};
}
}
