// Compile-time contract for platform/producer_view.h. It includes only the neutral header
// and standard headers, so a stray renderer or gamez dependency added to the header fails
// here first. This file has no runtime checks, registry entries or main(): mw3tests
// already provides those, and this file only needs to compile.
#include "platform/producer_view.h"

#include <cstddef>
#include <cstdint>
#include <type_traits>

namespace {

using platform::MissionIdentity;
using platform::ProducerPurpose;
using platform::ProducerView;

// MissionIdentity moved from render3d.h unchanged. These pin its ABI, which mission
// notifications and adapter checks already depend on: two int32 fields in this order.
static_assert(sizeof(MissionIdentity) == 8, "MissionIdentity stays two int32 fields");
static_assert(offsetof(MissionIdentity, world_index) == 0, "world_index first");
static_assert(offsetof(MissionIdentity, number) == 4, "number second");
static_assert(std::is_same<decltype(MissionIdentity::world_index), int32_t>::value, "int32");
static_assert(std::is_same<decltype(MissionIdentity::number), int32_t>::value, "int32");
static_assert(std::is_standard_layout<MissionIdentity>::value, "standard layout");
static_assert(std::is_trivially_copyable<MissionIdentity>::value, "trivially copyable");
static_assert(std::is_aggregate<MissionIdentity>::value, "still an aggregate");

// {-1, 0} is the empty identity a default value must produce.
constexpr MissionIdentity kDefaultIdentity{};
static_assert(kDefaultIdentity.world_index == -1, "empty world index");
static_assert(kDefaultIdentity.number == 0, "empty mission number");

// The purpose tag is an owned fixed-width value, safe to copy into packets.
static_assert(std::is_same<std::underlying_type<ProducerPurpose>::type, uint32_t>::value,
              "fixed-width purpose tag");
static_assert(std::is_trivially_copyable<ProducerPurpose>::value, "trivial purpose");
static_assert(static_cast<uint32_t>(ProducerPurpose::Original) == 0, "Original is the default");

// The record travels by value through queues and worker packets.
static_assert(std::is_trivially_copyable<ProducerView>::value, "owned by-value record");
static_assert(std::is_standard_layout<ProducerView>::value, "plain named fields only");
static_assert(!std::is_polymorphic<ProducerView>::value, "no vtable pointer");

// A default record is absent Original metadata, so baseline behaviour applies.
constexpr ProducerView kDefaultView{};
static_assert(!kDefaultView.present, "default record is absent");
static_assert(kDefaultView.purpose == ProducerPurpose::Original, "default purpose");
static_assert(kDefaultView.record_version == platform::kProducerViewRecordVersion, "version");
static_assert(!kDefaultView.canvas_available && !kDefaultView.camera_rect_available,
              "no fabricated viewport domains");

}  // namespace
