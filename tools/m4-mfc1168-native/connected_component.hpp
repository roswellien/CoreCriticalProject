#pragma once
#include "connected_entry.hpp"
#include "connected_address_contract.hpp"
#include <memory>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace mw34::m4_mfc1168_connected {
using Sink=void(*)(std::string_view,std::span<const std::byte>,void*);
struct Mapping {unsigned address{},permissions{};std::vector<std::byte>before;};
struct PointerCell {unsigned address{},before{},projected{};};
struct MergeCell {unsigned address{},before{},projected{};};
struct ImportProjection {unsigned pc{},cell{},raw{},projected{};};
struct Inputs {
 AddressDomain addresses{};
 unsigned guest_thread{},guest_CS{};
 std::array<std::vector<std::byte>,5>borrowed_before;
 std::array<std::byte,24>CS_before{};
 std::vector<Mapping>new_mappings;
 std::array<PointerCell,6>pointer_cells{};
 std::array<MergeCell,3>CRT_cells{};
 std::array<ImportProjection,7>imports{};
 std::string original_prefix_receipt_sha256,source_domain_receipt_sha256;
};

// There is deliberately no constructor/factory available in this revision.
// A separate chronological input authority must authenticate the carried
// prefix, complete BEFORE graph and exact merge/noninterference proof first.
class InputAuthority;
class ChronologicalAdmission {
 friend class InputAuthority;
 friend class Component;
 friend void materialize_loader_inputs(Runtime&,const Inputs&,const ChronologicalAdmission&);
 Runtime *runtime_{};const Inputs *inputs_{};
 std::string digest_;
 ChronologicalAdmission(Runtime&r,const Inputs&i,std::string digest):runtime_(&r),inputs_(&i),digest_(std::move(digest)){}
 public:
 ChronologicalAdmission(const ChronologicalAdmission&)=delete;
 ChronologicalAdmission&operator=(const ChronologicalAdmission&)=delete;
};

// Add new mappings plus six typed pointer projections and three proved CRT
// cells on a complete GuestMemory copy, then commit once. Existing IAT cells,
// FS head/bounds/self, registry cells, State, CPU and FX are never replaced.
// Call only before registry bootstrap captures its complete source-page mirror.
void materialize_loader_inputs(Runtime&,const Inputs&,const ChronologicalAdmission&);

class Component final:public Invocation {
 public:
 struct Impl;
 private:
 std::unique_ptr<Impl>impl_;
 public:
 Component(Runtime&,const Inputs&,const ChronologicalAdmission&,Sink,void*);
 ~Component()override;
 Component(const Component&)=delete;Component&operator=(const Component&)=delete;
 Runtime&runtime()noexcept override;
 void authority()override;
 void execute_literal(State&,unsigned frame,unsigned return_pc)override;
 void finish();
 void cleanup_failed();
 void checkpoint(std::string_view);
};
} // namespace mw34::m4_mfc1168_connected
