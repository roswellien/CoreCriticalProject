#include "check.h"
#include "crt/msvc_rand.h"
#include "gamez/zclass/cls_node.h"
#include "gamez/zclass/cls_data.h"
#include "gamez/zclass/cls_zbd.h"
#include "gamez/zclass/list.h"
#include "gamez/zclass/object3d.h"
#include "gamez/zmodel/gmod_const.h"
#include "gamez/zmodel/gmod_init.h"
#include "gamez/zmath/zmth_matrix.h"
#include "mech3/mech.h"
#include "mech3/mech_skin.h"
#include "mech3/veh_basic_object.h"
#include "mech3/veh_controls.h"
#include "mech3/veh_move.h"
#include <array>
#include <cfenv>
#include <cstring>
#include <limits>

namespace {
struct IsolatedFixtureNodes {
  zcls::NodePool pool=std::move(zcls::nodes());
  zcls::Lists lists=std::move(zcls::lists());
  zcls::Frames frames=zcls::frames();
  IsolatedFixtureNodes() {
    zcls::nodes()=zcls::NodePool{};
    zcls::lists()=zcls::Lists{};
  }
  ~IsolatedFixtureNodes() {
    zcls::classes_reset();
    zcls::nodes()=std::move(pool);
    zcls::lists()=std::move(lists);
    zcls::frames()=frames;
  }
};
}
TEST(fixture_native_allocation_import_and_bulk_lifetime) {
  IsolatedFixtureNodes isolated;
  auto* first=zcls::node_alloc();
  const auto first_id=first->fixture_life;
  EXPECT(first_id!=0 && bool(zcls::fixture_source_proof(first_id)));
  unsigned char saved[0xd0];
  std::memcpy(saved,first->raw,sizeof saved);
  const auto link=first->link;
  zcls::fixture_source_proof(first_id);
  EXPECT(std::memcmp(saved,first->raw,sizeof saved)==0 && first->link==link);
  zcls::node_unlist(first);
  zcls::node_slot_free(first);
  EXPECT(!zcls::fixture_source_proof(first_id));
  auto* reused=zcls::node_alloc();
  EXPECT(reused==first && reused->fixture_life!=first_id);
  const auto reused_id=reused->fixture_life;
  const auto reused_proof=*zcls::fixture_source_proof(reused_id);
  zcls::invalidate_world_source_proofs();
  EXPECT(!zcls::fixture_source_proof(reused_id));
  auto* after_load=zcls::node_alloc();
  const auto loaded_proof=*zcls::fixture_source_proof(after_load->fixture_life);
  EXPECT(loaded_proof.pool_epoch==reused_proof.pool_epoch &&
         loaded_proof.load_epoch!=reused_proof.load_epoch);
  // Import really overwrites a live address, bypassing node_alloc. A complete
  // authored class5 slot must receive its own new lifetime after read_node.
  zcls::node_unlist(reused);
  zcls::node_unlist(after_load);
  std::FILE* file=std::tmpfile();
  EXPECT(file!=nullptr);
  if(!file) return;
  zcls::Node stored{};
  stored.put<int32_t>(0x34,5);
  stored.put<int32_t>(0x3c,-1);
  stored.set_flags(4);
  stored.link=zcls::kNodeLive;
  zcls::Object3d data{};
  std::fwrite(stored.raw,sizeof stored.raw,1,file);
  std::fwrite(&stored.link,sizeof stored.link,1,file);
  std::fwrite(data.raw,sizeof data.raw,1,file);
  std::rewind(file);
  const auto before_import=after_load->fixture_life;
  EXPECT(zcls::read_nodes(1,file)>0);
  std::fclose(file);
  auto* imported=zcls::node_at(0);
  EXPECT(imported->fixture_life && imported->fixture_life!=first_id &&
         imported->fixture_life!=reused_id && !zcls::fixture_source_proof(before_import));
  const auto imported_id=imported->fixture_life;
  EXPECT(zcls::fixture_source_proof(imported_id)->pool_epoch!=loaded_proof.pool_epoch);
  zcls::classes_reset();
  EXPECT(!zcls::fixture_source_proof(imported_id));
  auto* reset=zcls::node_alloc();
  EXPECT(reset->fixture_life!=imported_id);
  const auto reset_id=reset->fixture_life;
  zcls::node_unlist(reset);
  zcls::free_node(0);
  EXPECT(!zcls::fixture_source_proof(reset_id));
}
TEST(fixture_vehicle_native_branch_pose_and_byte_preservation) {
  IsolatedFixtureNodes isolated;
  auto* parent=zcls::object3d_create();
  auto* root=zcls::object3d_create();
  auto* healthy=zcls::object3d_create();
  auto* destroyed=zcls::object3d_create();
  auto* lamp=zcls::object3d_create();
  auto* rear=zcls::object3d_create();
  zcls::node_set_name(healthy,"healthy");
  zcls::node_set_name(destroyed,"destroyed");
  zcls::node_link(parent,root);
  zcls::node_link(root,healthy);
  zcls::node_link(root,destroyed);
  zcls::node_link(healthy,lamp);
  zcls::node_link(destroyed,rear);
  mech3::Vehicle owner{};
  owner.node=root;
  owner.transform=zcls::object3d_matrix(root);
  owner.centroid=owner.target_node=root;
  zcls::node_tree_bind(root,&owner,0x80000,0);
  const auto lamp_id=lamp->fixture_life;
  const auto root_id=root->fixture_life;
  const auto healthy_id=healthy->fixture_life;
  auto proof=*zcls::fixture_source_proof(lamp_id);
  EXPECT(proof.vehicle_root==root_id && proof.healthy_root==healthy_id && !proof.destroyed_path);
  EXPECT(zcls::fixture_source_proof(rear->fixture_life)->destroyed_path);
  EXPECT(!zcls::fixture_vehicle_proof(root_id)); // Binding alone cannot activate a lamp.
  unsigned char saved[0xd0];
  std::memcpy(saved,root->raw,sizeof saved);
  const auto saved_link=root->link;
  const auto rng=crt::msvc_rand_state();
  std::fenv_t environment;
  std::fegetenv(&environment);
  std::fesetround(FE_DOWNWARD);
  std::feclearexcept(FE_ALL_EXCEPT);
  std::feraiseexcept(FE_DIVBYZERO);
  const auto exceptions=std::fetestexcept(FE_ALL_EXCEPT);
  zcls::fixture_vehicle_register(&owner,root,owner.active,owner.transform);
  zcls::fixture_observe_world(root,owner.transform);
  auto vehicle=*zcls::fixture_vehicle_proof(root_id);
  EXPECT(vehicle.registered && vehicle.active && vehicle.pose_valid && vehicle.world_valid);
  EXPECT(std::fegetround()==FE_DOWNWARD && std::fetestexcept(FE_ALL_EXCEPT)==exceptions);
  EXPECT(std::memcmp(saved,root->raw,sizeof saved)==0 && root->link==saved_link &&
         crt::msvc_rand_state()==rng);
  std::fesetenv(&environment);
  // Exercise the existing native callback itself, including its existing
  // marker work. No new node_to_world call is made by fixture observation.
  const auto saved_stack=zmth::matrix_stack();
  owner.transform[9]=12;
  owner.entity_moved();
  vehicle=*zcls::fixture_vehicle_proof(root_id);
  EXPECT(vehicle.local_pose[9]==12 && vehicle.pose_revision>1 &&
         vehicle.transform_revision==zcls::fixture_source_proof(root_id)->transform_revision);
  zmth::matrix_stack()=saved_stack;
  {
    zcls::FixtureWalkScope root_scope(root), healthy_scope(healthy), lamp_scope(lamp);
    const auto ancestry=zcls::fixture_ancestry();
    EXPECT(ancestry.supported && ancestry.nodes.size()==3 && ancestry.nodes.back().life==lamp_id);
  }
  zcls::node_set_active(healthy,0);
  EXPECT(!zcls::fixture_source_proof(healthy_id)->active);
  zcls::fixture_vehicle_state(root,false);
  EXPECT(!zcls::fixture_vehicle_proof(root_id)->active);
  zcls::node_tree_unbind(root,&owner,0x80000,0);
  EXPECT(zcls::fixture_source_proof(lamp_id)->vehicle_root==0);
  // Unregister after the game has already cleared its node still retires the
  // exact recorded registration; an address does not stand in for lifetime.
  owner.node=nullptr;
  zcls::fixture_vehicle_unregister(&owner);
  EXPECT(!zcls::fixture_vehicle_proof(root_id));
}
TEST(fixture_model_revision_replacement_and_address_reuse) {
  IsolatedFixtureNodes isolated;
  auto* node=zcls::object3d_create();
  zmod::Model first{},second{};
  std::memset(first.header,0x23,sizeof first.header);
  unsigned char header[sizeof first.header];
  std::memcpy(header,first.header,sizeof header);
  first.fixture_revision=std::make_shared<const int>(0);
  std::weak_ptr<const int> old=first.fixture_revision;
  first.invalidate_render_geometry();
  EXPECT(old.expired() && std::memcmp(header,first.header,sizeof header)==0);
  std::memset(first.header,0,sizeof first.header);
  zcls::node_set_model(node,&first);
  const auto before=*zcls::fixture_source_proof(node->fixture_life);
  zcls::node_set_model(node,&second);
  EXPECT(zcls::fixture_source_proof(node->fixture_life)->source_revision>before.source_revision);
  first.fixture_revision=std::make_shared<const int>(0);
  old=first.fixture_revision;
  first=zmod::Model{};
  EXPECT(old.expired());
  zcls::node_set_model(node,nullptr);
}

TEST(fixture_shared_material_mapping_and_unrelated_retention) {
  zmod::Material shared{},unrelated{};
  shared.flags=unrelated.flags=1;
  zmod::Polygon first_polygon{},second_polygon{},third_polygon{};
  first_polygon.material=second_polygon.material=&shared;
  third_polygon.material=&unrelated;
  zmod::Model first{},second{},third{};
  first.polygons=&first_polygon;
  second.polygons=&second_polygon;
  third.polygons=&third_polygon;
  shared.fixture_revision=std::make_shared<const int>(0);
  unrelated.fixture_revision=std::make_shared<const int>(0);
  std::weak_ptr<const int> first_receipt=first_polygon.material->fixture_revision;
  std::weak_ptr<const int> second_receipt=second_polygon.material->fixture_revision;
  std::weak_ptr<const int> third_receipt=third_polygon.material->fixture_revision;
  EXPECT(zmod::cycle_set_on(&first,2)==0);
  EXPECT(first_receipt.expired() && second_receipt.expired() && !third_receipt.expired());
  shared.fixture_revision=std::make_shared<const int>(0);
  first_receipt=shared.fixture_revision;
  zimg::TextureEntry texture{};
  EXPECT(zmod::cycle_set_map(&second,&texture)==1);
  EXPECT(first_receipt.expired() && !third_receipt.expired());
  shared.fixture_revision=std::make_shared<const int>(0);
  first_receipt=shared.fixture_revision;
  zmod::cycle_reset(&second);
  EXPECT(first_receipt.expired() && shared.texture==&texture && !third_receipt.expired());
  shared.fixture_revision=std::make_shared<const int>(0);
  first_receipt=shared.fixture_revision;
  zmod::cycle_set_frame(&first,0);
  EXPECT(first_receipt.expired() && !third_receipt.expired());
  first.fixture_revision=std::make_shared<const int>(0);
  third.fixture_revision=std::make_shared<const int>(0);
  std::weak_ptr<const int> first_model=first.fixture_revision,third_model=third.fixture_revision;
  EXPECT(zmod::model_set_scroll(&first,1,.25f,0)==0);
  EXPECT(first_model.expired() && !third_model.expired() && !third_receipt.expired());
  zmod::material_free(&shared);
  EXPECT(!third_receipt.expired());
  shared.fixture_revision=std::make_shared<const int>(0);
  first_receipt=shared.fixture_revision;
  zmod::material_init(shared);
  EXPECT(first_receipt.expired() && !third_receipt.expired());
  // Real table free/reuse and serialized replacement destroy the old stamp.
  auto saved_table=std::move(zmod::materials());
  zmod::materials()=zmod::MaterialTable{};
  auto* copied=zmod::material_copy(unrelated);
  EXPECT(!copied->fixture_revision); // Copy must never share C's lifetime.
  copied->fixture_revision=std::make_shared<const int>(0);
  first_receipt=copied->fixture_revision;
  zmod::material_free(copied);
  EXPECT(first_receipt.expired() && !third_receipt.expired());
  auto* reused=zmod::material_copy(unrelated);
  EXPECT(reused==copied && !reused->fixture_revision);
  reused->fixture_revision=std::make_shared<const int>(0);
  first_receipt=reused->fixture_revision;
  std::FILE* file=std::tmpfile();
  EXPECT(file!=nullptr);
  if(file) {
    // Header count0,size1,free0,used-1; one authored free material record.
    const std::int32_t table_header[]{1,0,0,-1};
    std::fwrite(table_header,sizeof table_header,1,file);
    unsigned char raw[0x2c]{};
    raw[1]=0x20;
    const std::int16_t end=-1;
    std::memcpy(raw+0x28,&end,2);
    std::memcpy(raw+0x2a,&end,2);
    std::fwrite(raw,sizeof raw,1,file);
    std::rewind(file);
    EXPECT(zmod::read_materials(file)>0);
    std::fclose(file);
    EXPECT(first_receipt.expired() && !third_receipt.expired());
  }
  zmod::materials()=std::move(saved_table);
  first.polygons=second.polygons=third.polygons=nullptr;
}

TEST(fixture_actual_skin_mapping_expires_only_affected_material) {
  const auto saved_globals=mech3::skin_globals();
  mech3::skin_globals().damage_mode=0;
  {
    mech3::Skin from("fixture-source",1),to("fixture-target",1);
    from.add_entry("fixture-original",nullptr);
    to.add_entry("fixture-next",nullptr);
    zimg::TextureEntry original{},replacement{};
    std::strcpy(original.name,"fixture-original");
    std::strcpy(replacement.name,"fixture-next");
    from.entries[0]->texture=&original;
    to.entries[0]->texture=&replacement;
    zmod::Material material{},unrelated{};
    material.flags=1;
    material.texture=&original;
    material.fixture_revision=std::make_shared<const int>(0);
    unrelated.fixture_revision=std::make_shared<const int>(0);
    const std::weak_ptr<const int> before=material.fixture_revision;
    const std::weak_ptr<const int> third=unrelated.fixture_revision;
    zmod::Polygon polygon{};
    polygon.material=&material;
    zmod::Model model{};
    const std::uint32_t count=1;
    std::memcpy(model.header+0x10,&count,4);
    model.polygons=&polygon;
    zcls::Node node{};
    node.model=&model;
    from.apply(&node,&to);
    EXPECT(material.texture==&replacement && before.expired() && !third.expired());
    material.fixture_revision=std::make_shared<const int>(0);
    const std::weak_ptr<const int> retiring=material.fixture_revision;
    zmod::material_free(&material);
    EXPECT(retiring.expired() && !third.expired());
  }
  mech3::skin_globals()=saved_globals;
}
TEST(fixture_actual_native_destroyed_and_death_branches) {
  IsolatedFixtureNodes isolated;
  auto* root=zcls::object3d_create();
  struct Controls : mech3::VehicleControls {
    unsigned queries{};
    bool destroyed() override { ++queries; return true; }
  } controls;
  struct Hooks : mech3::VehBasicHooks {
    uint32_t unported(const char*,std::initializer_list<zgame::Arg>) override { return 0; }
  } hooks;
  auto* previous=&mech3::veh_basic_hooks();
  mech3::set_veh_basic_hooks(&hooks);
  mech3::BasicVehicle owner{};
  owner.node=root;
  owner.transform=zcls::object3d_matrix(root);
  owner.controls=&controls;
  owner.ammo=nullptr;
  zcls::node_tree_bind(root,&owner,0x80000,0);
  zcls::fixture_vehicle_register(&owner,root,true,owner.transform);
  const auto id=root->fixture_life;
  mech3::vehicle_damage(owner,nullptr,0,0);
  EXPECT(!owner.active && !zcls::fixture_vehicle_proof(id)->active && controls.queries==1);
  owner.active=true;
  zcls::fixture_vehicle_state(root,true);
  mech3::vehicle_frame(owner,0);
  EXPECT(!owner.active && !zcls::fixture_vehicle_proof(id)->active && controls.queries==2);
  owner.active=true;
  zcls::fixture_vehicle_state(root,true);
  controls.health=10;
  controls.state=0;
  mech3::vehicle_die(owner);
  EXPECT(!owner.active && controls.health==0 && controls.state==4 &&
      !zcls::fixture_vehicle_proof(id)->active && controls.queries==2);
  zcls::fixture_vehicle_unregister(&owner);
  mech3::set_veh_basic_hooks(previous);
}
