#pragma once
#include <cstdint>
#include <cstring>
#include <type_traits>

// Neutral value types shared by the GameZ producer and every renderer. This header is
// included by render3d.h and (later) by the Core Draw definition, so it must stay free of
// renderer, SDL, Windows, Vulkan and gamez includes; anything heavier would create an
// include cycle or drag platform code into the Core packet types.
namespace platform {

// Typed mission-change notification: the 0-based campaign world (launch
// index) and the mission number within it. {-1, 0} is the empty identity
// (failed load, non-campaign game type or scene reset).
struct MissionIdentity {
  int32_t world_index = -1;
  int32_t number = 0;
};

inline MissionIdentity make_mission_identity(int32_t game_type,
                                             int32_t world_index,
                                             int32_t number,
                                             bool load_success) {
  // IA and multiplayer numbers name iaN/mpN blocks, not campaign mN blocks.
  if (!load_success || (game_type != 1 && game_type != 4)) {
    return MissionIdentity{-1, 0};
  }
  return MissionIdentity{world_index, number};
}

// Layout version of ProducerView. A consumer that sees any other value must treat the
// record as foreign provenance, not guess at its fields. Bump it whenever a field is
// added, removed or reinterpreted.
constexpr uint32_t kProducerViewRecordVersion = 1;

// Which producer call emitted a draw. Original is also the value for "no typed view":
// untyped, nested and flush-time draws keep today's baseline behaviour.
enum class ProducerPurpose : uint32_t { Original = 0, MainWorld = 1, WorldZoom = 2 };

// Field-for-field copy of zmth::Projection. It is repeated here rather than included so
// this header does not depend on gamez. The producer copies each float's bits as they
// are, which keeps stale inverses, signed zeros, NaN payloads and infinities exactly as
// the game left them. Nothing here may recompute, clamp or check them.
struct ProducerProjection {
  float origin_x = 0, origin_y = 0;
  float half_w = 0, half_h = 0;
  float cot_h = 0, cot_v = 0;
  float inv_cot_h = 0, inv_cot_v = 0;
  float inv_fx = 0, inv_fy = 0;
  float fov_h = 0, fov_v = 0;
  float near_z = 0;
  float cx = 0, cy = 0;
  float inv_near = 0;
  float far_z = 0;
  float fy_near = 0;
  float fx = 0, fy = 0;
  float fx_near = 0;
};
// 21 floats, matching zmth::Projection. The capture site should also assert equal size
// against the real type, since this header cannot see it.
static_assert(sizeof(ProducerProjection) == 21 * sizeof(float), "mirrors zmth::Projection");

// Field-for-field copy of the authored zmod::Fog, the game's values, not the device
// fog. zrndr::DeviceFog is deliberately not copied: it holds a send-function pointer,
// and a pointer must never ride in an owned packet. fog_set_near/far/alt_* keep their
// old inverses when the ranges are equal, so inv_range and inv_alt may be stale on
// purpose. Copy the bits; never rebuild them.
struct ProducerFog {
  int32_t on = 0;
  int32_t linear = 0;
  float color[3] = {};
  float near_range = 0;
  float near_sq = 0;
  float far_range = 0;
  float far_sq = 0;
  float inv_range = 0;
  float alt_high = 0;
  float alt_low = 0;
  float inv_alt = 0;
  float density = 0;
};
static_assert(sizeof(ProducerFog) == 14 * 4, "mirrors zmod::Fog");

// An integer pixel rectangle captured when the producer set it up. It is a copy, never a
// handle to a backend viewport or a reason to query one later.
struct ProducerRect {
  int32_t x = 0;
  int32_t y = 0;
  int32_t width = 0;
  int32_t height = 0;
};

// The producer-owned view a draw was emitted under, carried by value from enqueue to the
// render worker. Ownership rule: the record owns all of its bytes. It holds no pointer,
// callback, Node/Camera/renderer or shared owner, so a queued or posted copy stays valid
// after the producer's globals change, the mission resets or the producer is torn down.
//
// Bit preservation: every float is stored exactly as captured. Storing one does no
// arithmetic, so it cannot raise FP flags or depend on rounding mode. Numeric policy
// (finite checks, fallbacks) belongs to the consumer that reads a field, never to this
// record.
//
// Equality below compares named fields, floats by their uint32 bits through
// memcpy, never float== or a whole-struct memcmp that would read padding.
struct ProducerView {
  // Provenance. A default record is absent (present == false) with purpose Original.
  uint32_t record_version = kProducerViewRecordVersion;
  ProducerPurpose purpose = ProducerPurpose::Original;
  bool present = false;
  // The producer issues these. A typed record carries nonzero values, so a reset can tell
  // a stale queued binding from a live one.
  uint64_t producer_generation = 0;
  uint64_t mission_epoch = 0;
  // The exact identity in force when the draw was produced, including the empty {-1, 0}.
  MissionIdentity mission{};

  // Camera state at enqueue time. The camera is zmth::view().camera's 12 floats, already
  // wrap-adjusted by the producer, so a consumer must not translate it again.
  ProducerProjection projection{};
  float camera[12] = {};
  // The original near clip plane, kept apart from projection.near_z because the model
  // path consumes it separately (ModelDrawContext::clip_near).
  float clip_near = 0;

  // Two different domains. The canvas is the input viewport TL coordinates map through;
  // the camera rect is the possibly smaller zoom window set_camera projects into. Using
  // one for the other stretches a zoom view across the frame. An unavailable domain
  // means "not captured" (use baseline behaviour), not corrupt provenance, and its rect
  // bytes are then meaningless.
  bool canvas_available = false;
  ProducerRect canvas{};
  bool camera_rect_available = false;
  ProducerRect camera_rect{};

  // Authored fog, plus the effective DrawState.fog bit at enqueue. They are kept apart so
  // later policy can tell "authored off" from a cell's temporary effective-off state.
  ProducerFog fog{};
  bool draw_state_fog = false;
};

// Copying by value into Scene draws, worker packets and fixed queue slots relies on these.
static_assert(std::is_trivially_copyable<ProducerView>::value, "owned by-value record");
static_assert(std::is_standard_layout<ProducerView>::value, "plain named fields only");

// Compare named storage only. Float comparison must neither canonicalize NaNs
// and signed zero nor raise FP exceptions; padding is never part of identity.
inline bool same_producer_view_bits(const ProducerView& a, const ProducerView& b) {
  const auto bits = [](float x, float y) {
    uint32_t left, right;
    std::memcpy(&left, &x, sizeof left);
    std::memcpy(&right, &y, sizeof right);
    return left == right;
  };
  if (a.record_version != b.record_version || a.purpose != b.purpose ||
      a.present != b.present || a.producer_generation != b.producer_generation ||
      a.mission_epoch != b.mission_epoch ||
      a.mission.world_index != b.mission.world_index || a.mission.number != b.mission.number ||
      a.canvas_available != b.canvas_available || a.camera_rect_available != b.camera_rect_available ||
      a.draw_state_fog != b.draw_state_fog || !bits(a.clip_near, b.clip_near))
    return false;
  const auto rect = [](const ProducerRect& x, const ProducerRect& y) {
    return x.x == y.x && x.y == y.y && x.width == y.width && x.height == y.height;
  };
  if (!rect(a.canvas, b.canvas) || !rect(a.camera_rect, b.camera_rect)) return false;
#define PRODUCER_PROJECTION_EQUAL(field) if (!bits(a.projection.field, b.projection.field)) return false
  PRODUCER_PROJECTION_EQUAL(origin_x); PRODUCER_PROJECTION_EQUAL(origin_y);
  PRODUCER_PROJECTION_EQUAL(half_w); PRODUCER_PROJECTION_EQUAL(half_h);
  PRODUCER_PROJECTION_EQUAL(cot_h); PRODUCER_PROJECTION_EQUAL(cot_v);
  PRODUCER_PROJECTION_EQUAL(inv_cot_h); PRODUCER_PROJECTION_EQUAL(inv_cot_v);
  PRODUCER_PROJECTION_EQUAL(inv_fx); PRODUCER_PROJECTION_EQUAL(inv_fy);
  PRODUCER_PROJECTION_EQUAL(fov_h); PRODUCER_PROJECTION_EQUAL(fov_v);
  PRODUCER_PROJECTION_EQUAL(near_z); PRODUCER_PROJECTION_EQUAL(cx); PRODUCER_PROJECTION_EQUAL(cy);
  PRODUCER_PROJECTION_EQUAL(inv_near); PRODUCER_PROJECTION_EQUAL(far_z);
  PRODUCER_PROJECTION_EQUAL(fy_near); PRODUCER_PROJECTION_EQUAL(fx); PRODUCER_PROJECTION_EQUAL(fy);
  PRODUCER_PROJECTION_EQUAL(fx_near);
#undef PRODUCER_PROJECTION_EQUAL
  if (a.fog.on != b.fog.on || a.fog.linear != b.fog.linear) return false;
  for (unsigned i = 0; i < 12; ++i) if (!bits(a.camera[i], b.camera[i])) return false;
  for (unsigned i = 0; i < 3; ++i) if (!bits(a.fog.color[i], b.fog.color[i])) return false;
#define PRODUCER_FOG_EQUAL(field) if (!bits(a.fog.field, b.fog.field)) return false
  PRODUCER_FOG_EQUAL(near_range); PRODUCER_FOG_EQUAL(near_sq);
  PRODUCER_FOG_EQUAL(far_range); PRODUCER_FOG_EQUAL(far_sq); PRODUCER_FOG_EQUAL(inv_range);
  PRODUCER_FOG_EQUAL(alt_high); PRODUCER_FOG_EQUAL(alt_low); PRODUCER_FOG_EQUAL(inv_alt);
  PRODUCER_FOG_EQUAL(density);
#undef PRODUCER_FOG_EQUAL
  return true;
}

}  // namespace platform
