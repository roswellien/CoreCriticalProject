#pragma once
#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <memory>

#include "texture_source.hpp"

namespace mw34::texture_staging {
// Preserve the renderer's exact integer expansion, including floor division.
// Convert in CPU-cached memory, then copy contiguous blocks to write-combined
// Vulkan staging memory. No reads of mapped upload memory are required.
inline std::uint32_t expand(std::uint16_t p,unsigned format) {
    unsigned r,g,b,a;
    if(format==0){r=((p>>11)&31)*255/31;g=((p>>5)&63)*255/63;b=(p&31)*255/31;a=255;}
    else if(format==1){r=((p>>10)&31)*255/31;g=((p>>5)&31)*255/31;b=(p&31)*255/31;a=(p&0x8000)?255:0;}
    else {r=((p>>8)&15)*17;g=((p>>4)&15)*17;b=(p&15)*17;a=((p>>12)&15)*17;}
    return r|(g<<8)|(b<<16)|(a<<24);
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
// hold 16-bit data the game or the pack loader widened: bank textures through
// the game's bit replication (gamez/zvideo/zvid_ddd3d.cpp, expand), pack
// replacement images through `c * 255 / max` rounded down (frame_renderer.cpp,
// image_pixels, and expand() above). Dropping each channel's low bits undoes
// either widening exactly, so such a texture can go to the card at 2 bytes per
// texel and sample the same 16-bit values it came from.
enum class Pack16 : std::uint8_t { none, r5g6b5, a1r5g5b5, b4g4r4a4 };

// Bit flags for masks of 16-bit formats (which ones a device can use).
constexpr unsigned pack16_bit(Pack16 format) { return 1u << unsigned(format); }
constexpr unsigned kAllPack16 =
    pack16_bit(Pack16::r5g6b5) | pack16_bit(Pack16::a1r5g5b5) | pack16_bit(Pack16::b4g4r4a4);

namespace detail {
// A channel byte is exact for a candidate when widening its top bits back the
// candidate's way gives the same byte. Candidates are kept apart by widening,
// so a texture counts as 16-bit only when every texel came from the same one.
enum Candidate : unsigned {
  r5g6b5_replicated = 1u << 0,
  r5g6b5_rounded_down = 1u << 1,
  a1r5g5b5_replicated = 1u << 2,
  a1r5g5b5_rounded_down = 1u << 3,
  b4g4r4a4_any = 1u << 4, // 4-bit replication and `* 17` are the same widening
};
constexpr unsigned kR5G6B5 = r5g6b5_replicated | r5g6b5_rounded_down;
constexpr unsigned kA1R5G5B5 = a1r5g5b5_replicated | a1r5g5b5_rounded_down;

// The game's widening: the channel's bits repeated until they fill a byte.
constexpr bool replicates(unsigned byte, unsigned bits) {
  const unsigned top = byte >> (8 - bits);
  unsigned widened = top << (8 - bits);
  for (unsigned filled = bits; filled < 8; filled += bits)
    widened |= (top << (8 - bits)) >> filled;
  return widened == byte;
}
// The pack loader's widening: `c * 255 / max`, rounded down.
constexpr bool rounds_down(unsigned byte, unsigned bits) {
  const unsigned maximum = (1u << bits) - 1;
  return (byte >> (8 - bits)) * 255 / maximum == byte;
}

struct ExactTables {
  std::array<std::uint8_t, 256> red_blue{}, green{}, alpha{};
};
inline const ExactTables &exact_tables() {
  static const ExactTables tables = [] {
    ExactTables built;
    for (unsigned byte = 0; byte < 256; ++byte) {
      unsigned red_blue = 0, green = 0, alpha = 0;
      if (replicates(byte, 5)) {
        red_blue |= r5g6b5_replicated | a1r5g5b5_replicated;
        green |= a1r5g5b5_replicated;
      }
      if (rounds_down(byte, 5)) {
        red_blue |= r5g6b5_rounded_down | a1r5g5b5_rounded_down;
        green |= a1r5g5b5_rounded_down;
      }
      if (replicates(byte, 6))
        green |= r5g6b5_replicated;
      if (rounds_down(byte, 6))
        green |= r5g6b5_rounded_down;
      if (replicates(byte, 4)) {
        red_blue |= b4g4r4a4_any;
        green |= b4g4r4a4_any;
        alpha |= b4g4r4a4_any;
      }
      if (byte == 255)
        alpha |= kR5G6B5 | kA1R5G5B5;
      if (byte == 0)
        alpha |= kA1R5G5B5;
      built.red_blue[byte] = std::uint8_t(red_blue);
      built.green[byte] = std::uint8_t(green);
      built.alpha[byte] = std::uint8_t(alpha);
    }
    return built;
  }();
  return tables;
}
} // namespace detail

// The 16-bit format that holds every texel of an RGBA8 texture exactly (R, G,
// B, A bytes in memory order), preferring R5G6B5, then A1R5G5B5, then
// B4G4R4A4, among the formats in `allowed`; none when no allowed format does.
// It stops at the first texel no remaining candidate holds.
inline Pack16 exact_pack16(const std::uint32_t *rgba, std::size_t count, unsigned allowed) {
  unsigned remaining = 0;
  if (allowed & pack16_bit(Pack16::r5g6b5))
    remaining |= detail::kR5G6B5;
  if (allowed & pack16_bit(Pack16::a1r5g5b5))
    remaining |= detail::kA1R5G5B5;
  if (allowed & pack16_bit(Pack16::b4g4r4a4))
    remaining |= detail::b4g4r4a4_any;
  const auto &tables = detail::exact_tables();
  for (std::size_t index = 0; index < count && remaining; ++index) {
    const std::uint32_t texel = rgba[index];
    remaining &= tables.red_blue[texel & 0xff];
    remaining &= tables.green[(texel >> 8) & 0xff];
    remaining &= tables.red_blue[(texel >> 16) & 0xff];
    remaining &= tables.alpha[texel >> 24];
  }
  if (remaining & detail::kR5G6B5)
    return Pack16::r5g6b5;
  if (remaining & detail::kA1R5G5B5)
    return Pack16::a1r5g5b5;
  if (remaining & detail::b4g4r4a4_any)
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

// Writes an exact RGBA8 texture into staging at 16 bits: the inverse of both
// widenings above. Like copy(), it converts in CPU-cached memory and copies
// whole chunks, since staging memory is write-combined. native_texture_identity.hpp's
// canonical_upload_key keeps its own 16-bit packing for hashes; this one is only
// for the card.
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
// so the format follows it and the image is remade when that differs. During
// play, content can change every frame, so an image never narrows: it keeps
// its format while the content still fits it exactly, and otherwise becomes
// RGBA8, which never needs scanning again.
enum class Pack16Rule : std::uint8_t { from_content, keep_or_widen };
struct Pack16Choice {
  Pack16 pack{Pack16::none};
  bool recreate{};
};
// Called only for an upload that needs pixels and has them. `eligible` says
// the content is RGBA8 of the right size from a source may_pack16 allows.
inline Pack16Choice choose_pack16(Pack16Rule rule, bool has_image, Pack16 current, bool eligible,
                                  const std::uint32_t *rgba, std::size_t count, unsigned allowed) {
  if (!has_image) {
    const Pack16 wanted = eligible ? exact_pack16(rgba, count, allowed) : Pack16::none;
    return {wanted, false};
  }
  if (rule == Pack16Rule::from_content) {
    const Pack16 wanted = eligible ? exact_pack16(rgba, count, allowed) : Pack16::none;
    return {wanted, wanted != current};
  }
  if (current == Pack16::none)
    return {Pack16::none, false};
  const bool still_exact =
      eligible && exact_pack16(rgba, count, allowed & pack16_bit(current)) == current;
  if (still_exact)
    return {current, false};
  return {Pack16::none, true};
}
}
