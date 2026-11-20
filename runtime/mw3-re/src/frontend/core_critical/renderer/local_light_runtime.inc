
// Values only. The borrowed arguments below are consumed synchronously; the
// process trace keeps just serialized bytes and bounded record fingerprints.
struct FixtureTracePose {
  std::array<float,12> world{};
  float opacity{};
  bool available{},scope_available{},ordinary{},morphing{},overlay{};
  bool source_finite{true},float_range{true};
} fixture_trace_pose_;
struct FixtureTraceGeometry {
  std::size_t count{};
  std::uint64_t uv_hash{0xcbf29ce484222325ULL},position_hash{0xcbf29ce484222325ULL};
  std::array<float,4> uv_bounds{};
  bool uv_available{},uv_finite{true},uv_unit{true},positions_available{},positions_finite{true};
  const char* status{"geometry_unavailable"};
  void point(const float* position,const float* uv) {
    if(uv) {
      uv_hash=fixture_trace_hash(uv,2*sizeof(float),uv_hash);
      if(!std::isfinite(uv[0]) || !std::isfinite(uv[1])) uv_finite=false;
      else {
        uv_unit=uv_unit && uv[0]>=0 && uv[0]<=1 && uv[1]>=0 && uv[1]<=1;
        if(!count) uv_bounds={uv[0],uv[1],uv[0],uv[1]};
        else { uv_bounds[0]=std::min(uv_bounds[0],uv[0]); uv_bounds[1]=std::min(uv_bounds[1],uv[1]);
               uv_bounds[2]=std::max(uv_bounds[2],uv[0]); uv_bounds[3]=std::max(uv_bounds[3],uv[1]); }
      }
      uv_available=true;
    }
    if(position) {
      position_hash=fixture_trace_hash(position,3*sizeof(float),position_hash);
      positions_available=true;
      for(unsigned component=0;component<3;++component)
        positions_finite=positions_finite && std::isfinite(position[component]);
    }
    ++count;
  }
};
void fixture_trace_model(const ::platform::ModelDrawContext& context) {
  // begin_model_draw already holds VisualFloatScope; no renderer/game state
  // is changed by this owned copy, including when the normal fixture gate is off.
  fixture_trace_pose_={};
  fixture_trace_pose_.scope_available=true;
  fixture_trace_pose_.ordinary=context.ordinary;
  fixture_trace_pose_.morphing=context.morphing;
  fixture_trace_pose_.overlay=context.overlay;
  fixture_trace_pose_.opacity=context.opacity;
  fixture_trace_pose_.available=context.model_to_world!=nullptr;
  if(context.model_to_world)
    std::memcpy(fixture_trace_pose_.world.data(),context.model_to_world,12*sizeof(float));
}
void fixture_trace_emit(const char* producer,const zcls::Node* node,const zmod::Model* model,
    const zmod::Material* material,const zimg::TextureEntry* entry,
    std::optional<std::uint32_t> polygon,int texture,const FixtureTracePose& pose,
    const FixtureTraceGeometry& geometry,bool binding_current,
    const PreparedBatchDraw* prepared=nullptr) {
  auto& run=fixture_trace_run();
  if(!run.open() || current_mission_id_.empty()) return;
  VisualFloatScope preserve;
  FixtureTraceRecord record;
  record.append("[NATIVE_FIXTURE_SOURCE] {\"schema\":\"mw34.fixture-source.v1\",\"type\":\"source\"");
  record.text("producer",producer,std::strlen(producer));
  record.text("mission",current_mission_id_,64);
  record.append(",\"mission_world\":%d,\"mission_number\":%d,\"world_source_epoch\":%llu,"
      "\"group_epoch\":%llu,\"source_life\":%llu",
      current_mission_identity_.world_index,current_mission_identity_.number,
      (unsigned long long)zcls::world_source_epoch(),(unsigned long long)group_load_epoch_,
      (unsigned long long)(node ? node->fixture_life : 0));
  const auto proof=node ? zcls::fixture_source_proof(node->fixture_life) : std::nullopt;
  if(proof) record.append(",\"pool_epoch\":%llu,\"native_load_epoch\":%llu,\"source_revision\":%llu,"
      "\"transform_revision\":%llu,\"source_active\":%s,\"vehicle_root\":%llu,\"healthy_root\":%llu",
      (unsigned long long)proof->pool_epoch,(unsigned long long)proof->load_epoch,
      (unsigned long long)proof->source_revision,(unsigned long long)proof->transform_revision,
      proof->active ? "true":"false",(unsigned long long)proof->vehicle_root,
      (unsigned long long)proof->healthy_root);
  else record.append(",\"pool_epoch\":null,\"native_load_epoch\":null,\"source_revision\":null,"
      "\"transform_revision\":null,\"source_active\":null,\"vehicle_root\":null,\"healthy_root\":null");
  record.append(",\"node_class\":");
  if(node) record.append("%d",node->cls()); else record.append("null");
  const auto length=[](const char* text,std::size_t size) {
    return std::size_t(std::find(text,text+size,'\0')-text);
  };
  record.text("node_name",node ? node->name():nullptr,node ? length(node->name(),0x24):0,36);
  if(node && length(node->name(),0x24)==0x24) record.append(",\"node_name_unterminated\":true");
  record.append(",\"model_name\":null,\"material_name\":null,"
      "\"name_status\":\"native_Model_and_Material_have_no_name_fields\"");
  const auto* asset=node && node->source_asset ? node->source_asset.get() :
      (model ? model->world_source_asset.get() : nullptr);
  if(asset) {
    record.text("asset_name",asset->name,128);
    record.text("asset_member_sha256",asset->member_sha256,64);
  } else record.append(",\"asset_name\":null,\"asset_member_sha256\":null");
  if(asset && asset->world) {
    record.text("source_kind",asset->world->kind,64);
    record.text("source_member",asset->world->member,192);
    record.text("source_sha256",asset->world->sha256,64);
    record.append(",\"source_bytes\":%llu,\"asset_load_epoch\":%llu,\"model_slot\":%u",
        (unsigned long long)asset->world->bytes,(unsigned long long)asset->world->load_epoch,
        asset->world->model_slot);
  } else record.append(",\"source_kind\":null,\"source_member\":null,\"source_sha256\":null,"
      "\"source_bytes\":null,\"asset_load_epoch\":null,\"model_slot\":null");
  record.text("texture_name",entry ? entry->name : nullptr,entry ? length(entry->name,20):0,20);
  if(entry && length(entry->name,20)==20) record.append(",\"texture_name_unterminated\":true");
  const Texture* slot=texture>=0 && std::size_t(texture)<textures_.size() ? &textures_[texture] : nullptr;
  if(slot) {
    record.text("visible_texture_name",prepared && prepared->texture ? prepared->texture->name :
        (slot->replacement ? slot->replacement->name : slot->name),128);
    record.append(",\"texture_handle\":%d,\"texture_version\":%llu,\"texture_group_epoch\":%llu",
        texture,(unsigned long long)slot->version,(unsigned long long)slot->group_load_epoch);
  } else record.append(",\"visible_texture_name\":null,\"texture_handle\":null,"
      "\"texture_version\":null,\"texture_group_epoch\":null");
  std::optional<mw34::materials::SurfaceKey> original,visible;
  if(slot && slot->group_load_epoch==group_load_epoch_) {
    // A diagnostic must report malformed optional image data as unavailable,
    // rather than create a new exception path for an unknown source key.
    try { visible=fixture_visual_key(texture); } catch(const std::exception&) {}
    if(binding_current && !prepared && slot->surface_key.width && slot->surface_key.height && slot->surface_key.hash)
      original=slot->surface_key;
  }
  record.key("original_key",original ? &*original:nullptr);
  record.key("visible_key",visible ? &*visible:nullptr);
  const char* key_status=prepared ? "unavailable_prepared_batch_no_original_material_binding" :
      (original ? "current_original_texture_binding":"unavailable_original_texture_binding");
  record.text("original_key_status",key_status,std::strlen(key_status));
  record.append(",\"polygon\":");
  if(polygon) record.append("%u",*polygon); else record.append("null");
  record.append(",\"material_flags\":");
  if(material) record.append("%u",unsigned(material->flags)); else record.append("null");
  record.append(",\"material_alpha\":");
  if(material) record.append("%u",unsigned(material->alpha)); else record.append("null");
  record.text("geometry_status",geometry.status,std::strlen(geometry.status));
  record.append(",\"geometry_point_count\":%zu,\"original_corner_count\":",geometry.count);
  if(prepared) record.append("null"); else record.append("%zu",geometry.count);
  record.append(",\"uv_finite\":%s,\"uv_single_tile\":%s,\"positions_finite\":%s",
      geometry.uv_available ? (geometry.uv_finite ? "true":"false"):"null",
      geometry.uv_available && geometry.uv_finite ? (geometry.uv_unit ? "true":"false"):"null",
      geometry.positions_available ? (geometry.positions_finite ? "true":"false"):"null");
  const char* uv_source=prepared ? "prepared_batch":"original_polygon";
  record.text("uv_source",uv_source,std::strlen(uv_source));
  record.floats("visible_uv_bounds",geometry.uv_bounds.data(),4,geometry.uv_available && geometry.uv_finite);
  if(geometry.uv_available) record.hash("visible_uv_fingerprint",geometry.uv_hash);
  else record.append(",\"visible_uv_fingerprint\":null");
  record.floats("original_uv_bounds",geometry.uv_bounds.data(),4,!prepared && geometry.uv_available && geometry.uv_finite);
  if(!prepared && geometry.uv_available) record.hash("original_uv_fingerprint",geometry.uv_hash);
  else record.append(",\"original_uv_fingerprint\":null");
  if(geometry.positions_available && geometry.positions_finite) record.hash("local_position_fingerprint",geometry.position_hash);
  else record.append(",\"local_position_fingerprint\":null");
  bool pose_finite=pose.available && pose.source_finite;
  if(pose.float_range)
    for(float value:pose.world) pose_finite=pose_finite && std::isfinite(value);
  const bool pose_usable=pose_finite && pose.float_range;
  record.append(",\"pose_finite\":%s",pose.available ? (pose_finite ? "true":"false"):"null");
  record.append(",\"pose_float_range\":%s",pose.available && pose_finite ?
      (pose.float_range ? "true":"false"):"null");
  if(pose_usable) record.hash("owned_pose_fingerprint",fixture_trace_hash(pose.world.data(),sizeof pose.world));
  else record.append(",\"owned_pose_fingerprint\":null");
  record.floats("world_origin",pose.world.data()+9,3,pose_usable);
  if(pose_usable && geometry.positions_available && geometry.positions_finite)
    record.hash("owned_position_pose_fingerprint",fixture_trace_hash(pose.world.data(),sizeof pose.world,geometry.position_hash));
  else record.append(",\"owned_position_pose_fingerprint\":null");
  record.append(",\"model_scope_available\":%s,\"ordinary\":%s,\"morphing\":%s,\"overlay\":%s,\"opacity\":",
      pose.scope_available ? "true":"false",pose.scope_available ? (pose.ordinary ? "true":"false"):"null",
      pose.scope_available ? (pose.morphing ? "true":"false"):"null",
      pose.scope_available ? (pose.overlay ? "true":"false"):"null");
  if(pose.scope_available) record.scalar(pose.opacity); else record.append("null");
  record.append(",\"fixture_gate\":%s,\"active_world_view\":%s,\"hud\":%s,\"frontend_canvas\":%s,\"binding_current\":%s",
      fixture_producer_enabled() ? "true":"false",local_active_ ? "true":"false",
      scene_.hud ? "true":"false",scene_.frontend_canvas ? "true":"false",binding_current ? "true":"false");
  record.append(",\"prepared_alpha\":");
  if(prepared && prepared->batch) record.append("%u",unsigned(prepared->batch->color>>24));
  else record.append("null");
  const auto* surface=entry && entry->surface ? static_cast<const zvid::D3DTexture*>(entry->surface):nullptr;
  record.append(",\"native_texture_type\":");
  if(surface) record.append("%d",surface->type); else record.append("null");
  const auto* definition=visible ? mw34::native_fixtures::match(*visible):nullptr;
  const char* reason="catalog_scope_candidate";
  if(!binding_current && !prepared) reason="original_material_binding_mismatch";
  else if(!geometry.uv_available) reason=geometry.status;
  else if(!visible || !visible->hash) reason="visible_key_unavailable";
  else if(!fixture_producer_enabled()) reason="fixture_switch_or_lighting_disabled";
  else if(!local_active_) reason="outside_active_world_view";
  else if(!pose.float_range) reason="prepared_pose_outside_float_range";
  else if(!pose.scope_available) reason="native_model_scope_unavailable_prepared";
  else if(!pose.ordinary || pose.morphing || pose.overlay || !pose_finite || pose.opacity!=1.f)
    reason="model_scope_ineligible";
  else if(material && (!(material->flags&1) || material->alpha!=255)) reason="original_material_not_opaque_textured";
  else if(prepared && prepared->batch && (prepared->batch->color>>24)!=255) reason="prepared_batch_not_opaque";
  else if(surface && surface->type!=1) reason="unsupported_native_texture_type";
  else if(!definition) reason="catalog_miss";
  else if(!geometry.uv_finite || !geometry.uv_unit) reason="unsupported_nonfinite_or_repeating_uv";
  else if(definition->emission_only || definition->radius<=0) reason="catalog_glow_only";
  if(definition) {
    record.text("catalog_name",definition->name,std::strlen(definition->name),64);
    const bool vehicle=definition->classification==mw34::native_fixtures::Classification::vehicle_headlamp;
    record.append(",\"classification\":\"%s\",\"emission_only\":%s,\"radius\":",
        vehicle ? "vehicle_headlamp":"scenery",definition->emission_only ? "true":"false");
    record.scalar(definition->radius);
    record.append(",\"intensity\":");record.scalar(definition->intensity);
    record.append(",\"regions\":[");
    for(std::size_t index=0;index<definition->emission_regions.size();++index) {
      if(index) record.append(","); record.append("[");
      for(unsigned component=0;component<4;++component) {
        if(component) record.append(","); record.scalar(definition->emission_regions[index][component]);
      }
      record.append("]");
    }
    record.append("]");
    if(vehicle && std::strcmp(reason,"catalog_scope_candidate")==0) {
      const auto owner=proof ? zcls::fixture_vehicle_proof(proof->vehicle_root):std::nullopt;
      const auto healthy=proof ? zcls::fixture_source_proof(proof->healthy_root):std::nullopt;
      if(!owner || !owner->registered) reason="vehicle_owner_unregistered";
      else if(!owner->active) reason="vehicle_owner_inactive";
      else if(!healthy || !healthy->active || !healthy->healthy_branch) reason="vehicle_healthy_missing_or_inactive";
      else if(!owner->pose_valid || !owner->world_valid) reason="vehicle_owned_pose_unavailable";
    }
  } else record.append(",\"catalog_name\":null,\"classification\":null,\"emission_only\":null,\"radius\":null,\"intensity\":null,\"regions\":null");
  record.text("reason",reason,std::strlen(reason));
  record.append(",\"projection\":\"not_evaluated_by_diagnostic\",\"fingerprint\":\"fnv1a64_raw_float_bytes\"}");
  run.submit(record);
}
void fixture_trace_native(const char* producer,const ::platform::MaterialDrawContext& context,
                          int texture,const ::platform::ModelDrawContext* direct,
                          bool resource_current=true) {
  if(!fixture_trace_run().open() || current_mission_id_.empty()) return;
  const auto* node=direct ? static_cast<const zcls::Node*>(direct->node):native_context_.node;
  // One actual native source observation checks that optional diagnostics keep
  // the caller's FP/RNG/raw bytes. The normal adapter fixture exercises this
  // same path; this is not a parser-generated metadata stand-in.
  const bool check=node && !fixture_trace_run().native_control;
  const auto rounding=check ? std::fegetround():0;
  const auto exceptions=check ? std::fetestexcept(FE_ALL_EXCEPT):0;
  const auto random=check ? crt::msvc_rand_state():0;
  std::array<unsigned char,0xd0> raw{};
  const auto link=check ? node->link:0;
  if(check) std::memcpy(raw.data(),node->raw,raw.size());
  {
  VisualFloatScope preserve;
  if(!fixture_trace_run().claim()) return;
  const auto* model=direct ? (node ? node->model:nullptr):native_context_.model;
  auto pose=fixture_trace_pose_;
  if(direct) {
    pose={}; pose.scope_available=true; pose.available=direct->model_to_world!=nullptr;
    pose.ordinary=direct->ordinary;pose.morphing=direct->morphing;pose.overlay=direct->overlay;pose.opacity=direct->opacity;
    if(pose.available) std::memcpy(pose.world.data(),direct->model_to_world,sizeof pose.world);
  }
  FixtureTraceGeometry geometry;
  const zmod::Material* material=nullptr;
  const zimg::TextureEntry* entry=nullptr;
  bool current=resource_current && node && model && node->model==model && context.model==model &&
      model->polygons && model->count(0x10)<=4096 && context.polygon<model->count(0x10);
  if(current) {
    const auto& polygon=model->polygons[context.polygon];
    material=polygon.material;
    current=material && material==context.material && material->texture==context.texture_entry;
    if(current) {
      entry=material->texture;
      if(entry && entry->surface) {
        const auto* surface=static_cast<const zvid::D3DTexture*>(entry->surface);
        if(texture<0) texture=surface->handle;
        current=surface->handle==texture;
      } else current=false;
      const auto count=polygon.flags&255;
      if(count<3 || count>64) geometry.status="unsupported_original_corner_count";
      else if(!polygon.uvs) geometry.status="original_uv_unavailable";
      else {
        geometry.status="original_polygon_metadata";
        for(unsigned corner=0;corner<count;++corner) {
          const float* position=nullptr;
          if(model->vertices && polygon.vertex_indices && model->count(0x14)<=1048576 &&
              polygon.vertex_indices[corner]<model->count(0x14))
            position=model->vertices+std::size_t(polygon.vertex_indices[corner])*3;
          else { geometry.status="original_position_index_unavailable";geometry.positions_finite=false; }
          geometry.point(position,polygon.uvs+corner*2);
        }
      }
    }
  }
  fixture_trace_emit(producer,node,model,material,entry,context.polygon,texture,pose,geometry,current);
  }
  if(check) {
    if(std::fegetround()!=rounding || std::fetestexcept(FE_ALL_EXCEPT)!=exceptions ||
        crt::msvc_rand_state()!=random || node->link!=link ||
        std::memcmp(raw.data(),node->raw,raw.size())!=0)
      throw std::runtime_error("Fixture diagnostic changed native FP/RNG/source bytes");
    fixture_trace_run().native_control=true;
  }
}
void fixture_trace_prepared(const PreparedBatchDraw& source,int texture) {
  if(!fixture_trace_run().open() || current_mission_id_.empty()) return;
  VisualFloatScope preserve;
  if(!fixture_trace_run().claim()) return;
  auto pose=fixture_trace_pose_;
  pose.available=true;
  pose.world={};
  pose.source_finite=true;
  pose.float_range=true;
  constexpr std::array<unsigned,12> components{0,4,8,1,5,9,2,6,10,3,7,11};
  for(unsigned component=0;component<components.size();++component) {
    const double value=source.world[components[component]];
    if(!std::isfinite(value)) { pose.source_finite=false; continue; }
    const double magnitude=std::abs(value);
    if(magnitude>double(std::numeric_limits<float>::max()) ||
        (magnitude>0 && magnitude<double(std::numeric_limits<float>::denorm_min()))) {
      pose.float_range=false;
      continue;
    }
    // Prepared matrices are double; narrow only a finite, bounded diagnostic
    // copy. The original matrix and production fixture calculation are untouched.
    pose.world[component]=static_cast<float>(value);
    if(value!=0 && pose.world[component]==0) pose.float_range=false;
  }
  FixtureTraceGeometry geometry;
  if(source.batch && source.texture) {
    const auto& vertices=source.deformed.empty() ? source.batch->vertices:source.deformed;
    if(vertices.size()>4096*3) geometry.status="prepared_vertex_limit";
    else {
      geometry.status="prepared_batch_original_polygon_unavailable";
      for(const auto& vertex:vertices) geometry.point(vertex.data(),vertex.data()+6);
    }
  }
  fixture_trace_emit("prepared",pose.scope_available ? native_context_.node:nullptr,
      pose.scope_available ? native_context_.model:nullptr,nullptr,nullptr,
      std::nullopt,texture,pose,geometry,false,&source);
}

// Native source truth is independent of renderer attachment and copied on demand.
mw34::native_fixtures::VisibleSources local_fixture_sources_;
std::uint64_t fixture_observations_{}, fixture_rejections_{}, fixture_vehicle_pending_{};


// Producer cache is bounded independently of the per-Scene staging budget.
// Scene/worker payloads still contain only copied masks and the final Uniform.
std::vector<std::shared_ptr<const mw34::native_fixtures::Observation>> fixture_retained_;
std::vector<std::shared_ptr<const mw34::native_fixtures::Observation>> fixture_view_;
std::uint64_t fixture_expired_{}, fixture_retained_peak_{}, fixture_evictions_{};

std::optional<mw34::native_fixtures::Matrix> fixture_owner_world(
    const zcls::FixtureVehicleProof& vehicle, bool require_active = true) const {
  using namespace mw34::native_fixtures;
  if (!vehicle.registered || (require_active && !vehicle.active) || !vehicle.pose_valid || !vehicle.world_valid)
    return std::nullopt;
  const auto inverse = inverse_matrix(vehicle.observed_local);
  if (!inverse) return std::nullopt;
  // Keep the proven parent/world basis while replacing only the native root
  // local pose. Ancestor revisions below are required to remain unchanged.
  const auto parent = compose_matrix(*inverse, vehicle.observed_world);
  auto world = compose_matrix(vehicle.local_pose, parent);
  if (!inverse_matrix(world)) return std::nullopt;
  return world;
}

std::optional<mw34::native_fixtures::Matrix> fixture_validate(
    const mw34::native_fixtures::Observation& observation, bool require_active = true) {
  using namespace mw34::native_fixtures;
  if (!observation.proof) return identity_matrix; // Explicit visible-only source.
  const auto& proof = *observation.proof;
  if (proof.model_revision.expired() ||
      (proof.material_bound && proof.material_revision.expired()) || proof.texture < 0 ||
      std::size_t(proof.texture) >= textures_.size() || proof.texture_epoch != group_load_epoch_ ||
      textures_[proof.texture].version != proof.texture_version ||
      !(fixture_visual_key(proof.texture) == observation.key)) return std::nullopt;
  std::optional<zcls::FixtureVehicleProof> vehicle;
  if (proof.owner_root) {
    vehicle = zcls::fixture_vehicle_proof(proof.owner_root);
    const auto healthy = zcls::fixture_source_proof(proof.healthy_root);
    if (!vehicle || !healthy || (require_active && !healthy->active) || !healthy->healthy_branch ||
        healthy->destroyed_path || healthy->vehicle_root != proof.owner_root)
      return std::nullopt;
  }
  bool found_source=false, found_owner=!proof.owner_root, found_healthy=!proof.owner_root;
  unsigned healthy_branches=0;
  for (const auto& dependency : proof.dependencies) {
    const auto current = zcls::fixture_source_proof(dependency.life);
    if (!current || (require_active && !current->active) || current->pool_epoch != proof.pool_epoch ||
        current->load_epoch != proof.load_epoch ||
        current->source_revision != dependency.source_revision || current->destroyed_branch)
      return std::nullopt;
    if(proof.owner_root && current->healthy_branch && ++healthy_branches>1) return std::nullopt;
    found_source = found_source || current->life == proof.life;
    found_healthy = found_healthy || current->life == proof.healthy_root;
    if (current->life == proof.owner_root) {
      found_owner = true;
      if (!vehicle || vehicle->transform_revision != current->transform_revision)
        return std::nullopt; // A local mutation without the native pose callback.
    } else if (current->transform_revision != dependency.transform_revision) {
      return std::nullopt;
    }
  }
  if (!found_source || !found_owner || !found_healthy) return std::nullopt;
  return vehicle ? fixture_owner_world(*vehicle,require_active) : std::optional<Matrix>(identity_matrix);
}

std::shared_ptr<const mw34::native_fixtures::SourceProof> fixture_source_receipt(
    int texture, std::uint32_t polygon, bool retainable) {
  using namespace mw34::native_fixtures;
  const auto* node = native_context_.node;
  const auto* model = native_context_.model;
  if (!node || !model || !node->fixture_life) return {};
  const auto ancestry = zcls::fixture_ancestry();
  if (!ancestry.supported || ancestry.nodes.empty() ||
      ancestry.nodes.back().life != node->fixture_life) {
    fixture_reject("retention requires supported existing native ancestry; source remains per-view");
    return {};
  }
  const auto& source = ancestry.nodes.back();
  auto receipt = std::make_shared<SourceProof>();
  receipt->life = source.life;
  receipt->pool_epoch = source.pool_epoch;
  receipt->load_epoch = source.load_epoch;
  receipt->polygon = polygon;
  receipt->retainable = retainable;
  receipt->texture = texture;
  receipt->texture_epoch = group_load_epoch_;
  receipt->texture_version = textures_[texture].version;
  for (const auto& proof : ancestry.nodes) {
    if (!proof.active || proof.destroyed_path || proof.destroyed_branch) return {};
    receipt->dependencies.push_back({proof.life,proof.source_revision,proof.transform_revision});
  }
  const auto* definition = match(fixture_visual_key(texture));
  if (definition && definition->classification == Classification::vehicle_headlamp) {
    if (!source.vehicle_root || !source.healthy_root || source.destroyed_path) return {};
    receipt->owner_root = source.vehicle_root;
    receipt->healthy_root = source.healthy_root;
    auto vehicle = zcls::fixture_vehicle_proof(source.vehicle_root);
    if (!vehicle) return {};
    auto world = fixture_owner_world(*vehicle);
    if (!world) return {};
    receipt->owner_world = *world;
    if(!rigid_matrix(*world)) {
      receipt->retainable=false;
      fixture_reject("nonrigid vehicle world basis supports current geometry only");
    }
  }
  if (!model->fixture_revision) model->fixture_revision = std::make_shared<const int>(0);
  receipt->model_revision = model->fixture_revision;
  if(polygon != 0xffffffffU) {
    const auto* material=model->polygons[polygon].material;
    if(!material) return {};
    if(!material->fixture_revision) material->fixture_revision=std::make_shared<const int>(0);
    receipt->material_revision=material->fixture_revision;
    receipt->material_bound=true;
  }
  return receipt;
}

std::optional<mw34::native_fixtures::Observation> fixture_current_observation(
    const mw34::native_fixtures::Observation& source) {
  using namespace mw34::native_fixtures;
  const auto world = fixture_validate(source);
  if (!world) return std::nullopt;
  Observation result = source;
  if (!source.proof || !source.proof->owner_root) return result;
  const auto inverse = inverse_matrix(source.proof->owner_world);
  if (!inverse) return std::nullopt;
  const auto delta = compose_matrix(*inverse, *world);
  // A rigid copied pose preserves the authored outward offset and cone.
  // Scaling/reflection changes require a fresh original-geometry observation.
  if(!rigid_matrix(delta)) return std::nullopt;
  for(auto& entry : result.physical_lights) {
    auto& light = entry.light;
    const auto position = transform_point(delta,{light.start[0],light.start[1],light.start[2]});
    std::copy(position.begin(),position.end(),light.start.begin());
    if(light.end[3] == 0) {
      std::copy(position.begin(),position.end(),light.end.begin());
    } else if(light.end[3] == 2) {
      const auto direction = detail::unit_direction(transform_point(delta,
          {light.end[0],light.end[1],light.end[2]},true));
      std::copy(direction.begin(),direction.end(),light.end.begin());
    }
  }
  return result;
}

void fixture_remember(const std::shared_ptr<const mw34::native_fixtures::Observation>& observation) {
  const auto same = [&](const auto& entry) {
    if (!observation->proof || !entry->proof || !observation->proof->retainable ||
        !entry->proof->retainable) return entry == observation;
    return entry->proof->life == observation->proof->life &&
        entry->proof->polygon == observation->proof->polygon && entry->key == observation->key;
  };
  auto view = std::find_if(fixture_view_.begin(),fixture_view_.end(),same);
  if(view != fixture_view_.end()) *view=observation;
  else if(fixture_view_.size()<4096) fixture_view_.push_back(observation);
  else fixture_reject("per-view fixture observation limit reached");
  if(!observation->proof || !observation->proof->retainable || observation->physical_lights.empty()) return;
  auto retained = std::find_if(fixture_retained_.begin(),fixture_retained_.end(),same);
  if(retained != fixture_retained_.end()) *retained=observation;
  else {
    if(fixture_retained_.size()==256) {
      fixture_retained_.erase(fixture_retained_.begin());
      if(++fixture_evictions_==1) fixture_reject("retained source limit reached; oldest receipt evicted");
    }
    fixture_retained_.push_back(observation);
  }
  fixture_retained_peak_=std::max(fixture_retained_peak_,std::uint64_t(fixture_retained_.size()));
}

void fixture_refresh_sources() {
  local_fixture_sources_.clear();
  local_fixture_sources_.set_eye({local_camera_[3],local_camera_[7],local_camera_[11]});
  for(auto iterator=fixture_retained_.begin();iterator!=fixture_retained_.end();) {
    const auto current=fixture_current_observation(**iterator);
    if(current) { local_fixture_sources_.observe(*current); ++iterator; }
    else if(!fixture_validate(**iterator,false)) {
      iterator=fixture_retained_.erase(iterator);
      ++fixture_expired_;
    } else {
      // Activation is distinct from lifetime. A surviving source can switch
      // on again off camera without resurrecting a freed or replaced node.
      ++iterator;
    }
  }
  for(const auto& observation : fixture_view_)
    if(const auto current=fixture_current_observation(*observation))
      local_fixture_sources_.observe(*current);
}

bool fixture_producer_enabled() const {
  return lighting_.enabled && bridge_config_.effect_lights && bridge_config_.fixture_lights;
}

mw34::materials::SurfaceKey prepared_fixture_key(const ::platform::prepared::Image &image) const {
  if (!image.width || !image.height || image.width > 4096 || image.height > 4096 ||
      image.pixels.size() != std::size_t(image.width) * image.height)
    throw std::runtime_error("Prepared fixture image is not a complete RGB565 plane");
  // BWTEX1's declared image.hash is not authenticated by its reader. Derive
  // this admission key from every immutable pixel rather than trusting it.
  return {image.width, image.height, 1,
          mw34::materials::normal_hash(image.pixels.data(), image.pixels.size() * 2)};
}

mw34::materials::SurfaceKey fixture_visual_key(int texture) {
  if (texture < 0 || std::size_t(texture) >= textures_.size())
    return {};
  auto &slot = textures_[texture];
  if (slot.group_load_epoch != group_load_epoch_)
    return {};
  if (!slot.replacement)
    return slot.surface_key;
  if (!slot.fixture_visual_key)
    slot.fixture_visual_key = prepared_fixture_key(*slot.replacement);
  return *slot.fixture_visual_key;
}

void fixture_reject(const char *reason) {
  if (++fixture_rejections_ <= 8)
    std::fprintf(stderr, "[NATIVE_FIXTURE_REJECT] reason=%s\n", reason);
}

std::shared_ptr<const mw34::native_fixtures::Observation> fixture_observation(
    const mw34::materials::SurfaceKey &key,
    const std::vector<mw34::native_fixtures::UvPoint> &triangles,
    bool separate_triangles = false,
    std::shared_ptr<const mw34::native_fixtures::SourceProof> proof = {}) {
  VisualFloatScope guard;
  try {
    std::optional<mw34::native_fixtures::Point> forward;
    if (proof && proof->owner_root) {
      const auto& world=proof->owner_world;
      forward=mw34::native_fixtures::detail::unit_direction({-world[6],-world[7],-world[8]});
    }
    const auto result = mw34::native_fixtures::observe_source(
        key, triangles, mw34::native_fixtures::Winding::original, separate_triangles, forward);
    if (result.status == mw34::native_fixtures::ObservationStatus::vehicle_pending) {
      if (++fixture_vehicle_pending_ == 1)
        std::fprintf(stderr, "[NATIVE_FIXTURES] vehicle rejected: missing registered active healthy pose proof\n");
    } else if (result.status == mw34::native_fixtures::ObservationStatus::unsupported_mapping) {
      fixture_reject("repeating or nonfinite original UV mapping");
    }
    if (!result.value || !proof) return result.value;
    auto observation=std::make_shared<mw34::native_fixtures::Observation>(*result.value);
    observation->proof=std::move(proof);
    return fixture_validate(*observation) ? observation : nullptr;
  } catch (const std::invalid_argument &error) {
    fixture_reject(error.what());
    return {};
  }
}

void fixture_model_scope(const ::platform::ModelDrawContext &context) {
  native_context_.fixture_eligible = fixture_producer_enabled() && context.ordinary &&
      !context.morphing && !context.overlay && context.opacity == 1.f && context.model_to_world;
  if (!native_context_.fixture_eligible)
    return;
  const auto *matrix = context.model_to_world;
  for (unsigned index = 0; index < 12; ++index)
    if (!std::isfinite(matrix[index]))
      throw std::runtime_error("Fixture source has a nonfinite native transform");
  native_context_.fixture_world =
      {matrix[0], matrix[3], matrix[6], matrix[9], matrix[1], matrix[4], matrix[7], matrix[10],
       matrix[2], matrix[5], matrix[8], matrix[11], 0, 0, 0, 1};
}

std::shared_ptr<const mw34::native_fixtures::Observation>
capture_fixture_polygon(int texture) {
  if (!fixture_producer_enabled() || !local_active_)
    return {};
  const auto key = fixture_visual_key(texture);
  const auto *definition = mw34::native_fixtures::match(key);
  if (!definition)
    return {};

  const auto &context = native_context_;
  const auto *model = context.model;
  if (!context.fixture_eligible || !context.material_active || !context.node ||
      context.node->model != model || !model || context.material.model != model ||
      !model->polygons || !model->vertices || !model->count(0x10) || model->count(0x10) > 4096 ||
      context.material.polygon >= model->count(0x10) || !model->count(0x14) ||
      model->count(0x14) > 1048576 || model->count(0x1c)) {
    fixture_reject("missing supported original model/material scope");
    return {};
  }
  const auto &polygon = model->polygons[context.material.polygon];
  const auto *material = polygon.material;
  if (!material || context.material.material != material || !(material->flags & 1) ||
      material->alpha != 255 || !material->texture ||
      context.material.texture_entry != material->texture || !material->texture->surface ||
      !polygon.uvs || !polygon.vertex_indices) {
    fixture_reject("original fixture polygon/material mismatch");
    return {};
  }
  const auto *surface = static_cast<const zvid::D3DTexture *>(material->texture->surface);
  if (surface->handle != texture || surface->type != 1) {
    fixture_reject("original fixture texture handle/type mismatch");
    return {};
  }
  // Cycled material identity and scrolling/animated UVs have no retained
  // island contract. A current supported cycle can still be visible-only.
  const bool retainable = !(material->flags & 6) && !material->cycle && !material->file_cycle &&
      !(model->count(8) & 0x1c);
  if(!retainable) fixture_reject("cycled/animated material is per-view only; vehicle retention unsupported");
  auto receipt=fixture_source_receipt(texture, context.material.polygon, retainable);
  if(definition->classification == mw34::native_fixtures::Classification::vehicle_headlamp &&
      (!retainable || !receipt)) return fixture_observation(key, {});
  const unsigned corners = polygon.flags & 255;
  if (corners < 3 || corners > mw34::native_fixtures::maximum_polygon_corners) {
    fixture_reject("unsupported original fixture polygon size");
    return {};
  }
  std::vector<mw34::native_fixtures::UvPoint> points;
  points.reserve(corners);
  const auto &world = context.fixture_world;
  for (unsigned corner = 0; corner < corners; ++corner) {
    const unsigned index = polygon.vertex_indices[corner];
    if (index >= model->count(0x14)) {
      fixture_reject("original fixture position index outside model");
      return {};
    }
    const auto *position = model->vertices + std::size_t(index) * 3;
    mw34::native_fixtures::UvPoint point{};
    for (unsigned row = 0; row < 3; ++row)
      point.position[row] = float(world[row * 4] * position[0] + world[row * 4 + 1] * position[1] +
                                  world[row * 4 + 2] * position[2] + world[row * 4 + 3]);
    point.u = polygon.uvs[corner * 2];
    point.v = polygon.uvs[corner * 2 + 1];
    points.push_back(point);
  }
  try {
    return fixture_observation(key, mw34::native_fixtures::triangulate_polygon(points,
        polygon.flags & 0x400 ? mw34::native_fixtures::Topology::strip
                              : mw34::native_fixtures::Topology::fan), false, std::move(receipt));
  } catch (const std::invalid_argument &error) {
    fixture_reject(error.what());
    return {};
  }
}

std::shared_ptr<const mw34::native_fixtures::Observation> capture_fixture_range(
    const cc::geometry::Resource &resource, const ::platform::ModelDrawContext &context,
    const cc::geometry::Range &range, int texture) {
  VisualFloatScope guard;
  if(fixture_trace_run().open()) {
    const auto* node=static_cast<const zcls::Node*>(context.node);
    const auto* model=node ? node->model:nullptr;
    const auto* material=model && model->polygons && range.polygon<model->count(0x10) && model->count(0x10)<=4096
        ? model->polygons[range.polygon].material:nullptr;
    fixture_trace_native("native-direct",{model,material,material ? material->texture:nullptr,range.polygon},
        texture,&context,model && model->render_geometry.get()==&resource);
  }
  if (!fixture_producer_enabled() || !local_active_ ||
      !mw34::native_fixtures::match(fixture_visual_key(texture)))
    return {};
  struct Restore {
    NativeBindingContext &destination;
    NativeBindingContext saved;
    ~Restore() { destination = std::move(saved); }
  } restore{native_context_, native_context_};
  native_context_ = {};
  const auto *node = static_cast<const zcls::Node *>(context.node);
  const auto *model = node ? node->model : nullptr;
  if (!model || model->render_geometry.get() != &resource || !model->polygons ||
      range.polygon >= model->count(0x10) || resource.source_polygons != model->count(0x10) ||
      resource.source_vertices != model->count(0x14)) {
    fixture_reject("direct geometry is not its current original fixture resource");
    return {};
  }
  const auto *material = model->polygons[range.polygon].material;
  native_context_.node = node;
  native_context_.model = model;
  native_context_.material = {model, material, material ? material->texture : nullptr, range.polygon};
  native_context_.material_active = true;
  fixture_model_scope(context);
  return capture_fixture_polygon(texture);
}

std::shared_ptr<const mw34::native_fixtures::Observation>
capture_fixture_prepared(const PreparedBatchDraw &source, int texture) {
  VisualFloatScope guard;
  if(fixture_trace_run().open()) fixture_trace_prepared(source,texture);
  if (!fixture_producer_enabled() || !local_active_ || !source.batch || !source.texture ||
      (source.batch->color >> 24) != 255)
    return {};
  const auto key = fixture_visual_key(texture);
  if (!mw34::native_fixtures::match(key))
    return {};
  const auto &vertices = source.deformed.empty() ? source.batch->vertices : source.deformed;
  if (vertices.size() % 3 || vertices.size() > mw34::native_fixtures::maximum_triangles * 3) {
    fixture_reject("prepared fixture exceeds triangle-list contract");
    return {};
  }
  std::vector<mw34::native_fixtures::UvPoint> triangles;
  triangles.reserve(vertices.size());
  for (const auto &vertex : vertices) {
    mw34::native_fixtures::UvPoint point{};
    for (unsigned row = 0; row < 3; ++row)
      point.position[row] = float(source.world[row * 4] * vertex[0] +
          source.world[row * 4 + 1] * vertex[1] + source.world[row * 4 + 2] * vertex[2] +
          source.world[row * 4 + 3]);
    point.u = vertex[6];
    point.v = vertex[7];
    triangles.push_back(point);
  }
  // Prepared batches can carry donor-bone attachment transforms that the
  // native ancestry receipt does not describe. Observe per-view; do not retain.
  auto receipt=source.deformed.empty() ? fixture_source_receipt(texture, 0xffffffffU, false) : nullptr;
  return fixture_observation(key, triangles, true, std::move(receipt));
}

void apply_fixture_observation(vk::Draw &draw,
    const std::shared_ptr<const mw34::native_fixtures::Observation> &observation) {
  VisualFloatScope guard;
  if (!fixture_producer_enabled() || !local_active_ || !observation || !draw.count ||
      scene_.hud || scene_.frontend_canvas || draw.depth_only || draw.native_sky)
    return;
  const auto current=fixture_current_observation(*observation);
  if(!current) return;
  // Capture after the path's fog initialization and after copying any cached
  // draw. The returned index belongs to exactly this Scene, never its cache.
  apply_fixture_observation_emission(draw.push.fog, observation->intensity);
  draw.emission_index = scene_.emissions.capture(
      {float(observation->regions.size()), observation->intensity, 0, 0}, observation->regions);
  fixture_remember(observation);
  ++fixture_observations_;
}

std::shared_ptr<const mw34::native_fixtures::Observation> deferred_fixture_observation(int texture) {
  VisualFloatScope guard;
  if (!fixture_producer_enabled() || !local_active_ || texture < 0 ||
      std::size_t(texture) >= textures_.size())
    return {};
  if (!deferred_material_binding_)
    return capture_fixture_polygon(texture);
  const auto *binding = validated_deferred_binding(textures_[texture].surface_key, texture);
  return binding ? binding->fixture : nullptr;
}

// Producer-owned local light state; packets receive only the fixed Uniform.
mw34::effects::Catalog local_catalog_;
mw34::effects::ObservedLights local_observed_;
std::vector<mw34::effects::Candidate> local_native_;
std::vector<mw34::headlights::StockProfile> headlight_catalog_;
std::vector<mw34::effects::Candidate> headlight_candidates_;
mw34::headlights::PlayerState headlight_player_;
unsigned headlight_key_{};
std::size_t headlight_peak_{};
std::array<float, 6> local_projection_{};
std::array<float, 12> local_camera_{};
bool local_active_{};
double local_time_{};
std::uint64_t local_observations_{}, local_native_peak_{}, local_packet_peak_{};

void local_lights_load() {
  if (!bridge_config_.effect_lights) {
    if (bridge_config_.mech_headlights)
      fprintf(stderr, "[HEADLIGHTS] inactive: local lights disabled\n");
    return;
  }
  VisualFloatScope guard;
  if (!lighting_.enabled || bridge_config_.effect_light_catalog.empty())
    throw std::runtime_error("Local lights require lighting and a catalog");
  std::ifstream stream(
      std::filesystem::u8path(bridge_config_.effect_light_catalog),
      std::ios::binary);
  if (!stream)
    throw std::runtime_error("effect light catalog missing");
  auto composed = mw34::effects::read_catalog(stream);
  std::set<std::filesystem::path> catalog_paths{
      std::filesystem::u8path(bridge_config_.effect_light_catalog).lexically_normal()};
  if (environment_) {
    for (const auto &[region, resources] : environment_->resources) {
      const auto effects = resources.find(::platform::prepared::EnvironmentRole::effects);
      if (effects == resources.end())
        continue;
      const auto path = std::filesystem::u8path(effects->second).lexically_normal();
      if (!catalog_paths.insert(path).second)
        continue;
      std::ifstream pack(path, std::ios::binary);
      if (!pack)
        throw std::runtime_error("Selected pack effect light catalog missing");
      composed = mw34::effects::merge_catalogs(
          composed, mw34::effects::read_catalog(pack));
    }
  }
  local_catalog_ = std::move(composed);
  if (!bridge_config_.mech_headlights)
    return;
  if (bridge_config_.stock_headlights.empty()) {
    fprintf(stderr, "[HEADLIGHTS] inactive: no stock catalog selected\n");
    return;
  }
  std::ifstream catalog(std::filesystem::u8path(bridge_config_.stock_headlights),
                        std::ios::binary);
  if (!catalog)
    throw std::runtime_error("Headlights: cannot open stock catalog");
  headlight_catalog_ = mw34::headlights::read_stock_catalog(catalog);
  if (bridge_config_.headlight_bindings.empty()) {
    fprintf(stderr, "[HEADLIGHTS] inactive: no input binding selected\n");
    return;
  }
  std::ifstream bindings(std::filesystem::u8path(bridge_config_.headlight_bindings));
  std::string magic, extra;
  int button = -1;
  if (!(bindings >> magic >> headlight_key_ >> button) ||
      magic != "CC_MW3_HEADLIGHTS_V1" || headlight_key_ >= zin::kKeys ||
      (headlight_key_ && !(headlight_key_ & 255)) || button < -1 || button > 25 ||
      (bindings >> extra))
    throw std::runtime_error("Headlights: invalid input binding");
  const auto scan = headlight_key_ & 255;
  if (scan == 0x43 || scan == 0x44 || scan == 0x57)
    throw std::runtime_error("Headlights: key reserved for capture/replay");
  if (!headlight_key_ || headlight_catalog_.empty())
    fprintf(stderr, "[HEADLIGHTS] inactive: no keyboard binding or stock profile\n");
}

bool wants_player_headlight_ticks() const override {
  return headlight_key_ && !headlight_catalog_.empty() && !current_mission_id_.empty();
}

void player_headlight_tick(const ::platform::PlayerHeadlightTick &tick) override {
  VisualFloatScope guard;
  headlight_candidates_.clear();
  const auto *node = static_cast<const zcls::Node *>(tick.node);
  const auto *asset = node && node->source_asset_root ? node->source_asset.get() : nullptr;
  const auto *profile = asset ? mw34::headlights::match_original(
      headlight_catalog_, asset->name, asset->member_sha256) : nullptr;
  const auto &input = zin::state();
  const auto key = zin::key_state(headlight_key_);
  const bool pressed = (key & (zin::kPressed | zin::kHeld)) && !(key & zin::kReleased) &&
                       input.modifiers == (headlight_key_ & 0x700);
  headlight_player_.update(tick.generation, reinterpret_cast<std::uintptr_t>(node),
                           tick.tick, std::max(0.0f, tick.dt), tick.shutdown, pressed,
                           profile && tick.dt >= 0 && input.kbd_ready && !input.char_callback);
  const auto intensity = headlight_player_.owner.envelope.current;
  if (!profile || intensity <= 0)
    return;
  zmth::Mat34 world;
  zmth::push(&world);
  zmth::load_identity();
  const auto transformed = zcls::node_to_world(const_cast<zcls::Node *>(node), 1);
  zmth::pop();
  if (transformed)
    return;
  ::platform::ModelDrawContext context{};
  context.node = node;
  context.model_to_world = world.m;
  context.ordinary = true;
  for (std::size_t i = 0; i < profile->lamps.size(); ++i) {
    const auto &lamp = profile->lamps[i];
    if (headlight_player_.owner.retired_emitters.count(lamp.id))
      continue;
    std::optional<::platform::prepared::Matrix> pose;
    std::vector<std::uintptr_t> ancestry;
    if (lamp.space == "donor_bone") {
      pose = prepared_.donor_headlight_socket(context, lamp.attachment, &ancestry);
    } else {
      pose = original_headlight_socket(context, lamp.attachment, &ancestry);
    }
    if (!pose)
      continue;
    if (context.ordinary && !ancestry.empty()) {
      headlight_player_.owner.source_ancestry[lamp.id] = std::move(ancestry);
    }
    // Native fixture IDs occupy the low range, while weapons have a separate namespace.
    if (auto candidate = mw34::headlights::spotlight(lamp, *pose, intensity, (1ULL << 63) + i))
      headlight_candidates_.push_back(*candidate);
  }
  headlight_peak_ = std::max(headlight_peak_, headlight_candidates_.size());
}

void retire_headlight_node(std::uintptr_t node) override {
  headlight_player_.owner.retire_node(node, headlight_player_.owner.generation);
}

void local_lights_clear() {
  fixture_retained_.clear();
  fixture_view_.clear();
  local_fixture_sources_.clear();
  headlight_player_ = {};
  headlight_candidates_.clear();
  local_observed_.clear();
  local_native_.clear();
  local_active_ = false;
  local_camera_ = {};
  local_projection_ = {};
  local_time_ = 0.0;
}

void local_lights_begin() {
  fixture_view_.clear();
  local_fixture_sources_.clear();
  local_active_ = false;
  local_native_.clear();
  if (!bridge_config_.effect_lights || current_mission_id_.empty())
    return;
  VisualFloatScope guard;
  const auto p = zmth::projection();
  local_projection_ = {p.near_z, p.fx_near, p.fy_near, p.cx, p.cy, p.far_z};
  if (!std::isfinite(local_projection_[0]) ||
      !std::isfinite(local_projection_[1]) ||
      !std::isfinite(local_projection_[2]) ||
      !std::isfinite(local_projection_[3]) ||
      !std::isfinite(local_projection_[4]) ||
      !std::isfinite(local_projection_[5]))
    throw std::runtime_error("Local lights: non-finite projection");
  if (local_projection_[0] <= 0.0f || local_projection_[1] <= 0.0f ||
      local_projection_[2] <= 0.0f || local_projection_[5] <= 0.0f)
    throw std::runtime_error("Local lights: invalid projection");
  const float *m = zmth::view().camera.m;
  local_camera_ = {m[0], m[3],  m[6], m[9], m[1], m[4],
                   m[7], m[10], m[2], m[5], m[8], m[11]};
  for (float v : local_camera_)
    if (!std::isfinite(v))
      throw std::runtime_error("Local lights: invalid camera");
  local_time_ = ztimer::state().total_scaled;
  if (!std::isfinite(local_time_) || local_time_ < 0.0)
    throw std::runtime_error("Local lights: invalid time");
  if (bridge_config_.fixture_lights) {
    local_native_ = mw34::effects::collect_native_lights(zmod::light_list());
    local_native_peak_ = std::max(local_native_peak_,
                                  static_cast<uint64_t>(local_native_.size()));
  }
  local_active_ = true;
}

void local_lights_observe(const TLVertex *vertices, int count,
                          const DrawState &state) {
  if (!bridge_config_.effect_lights || !local_active_ || state.sharp ||
      state.texture < 0 ||
      state.texture >= static_cast<int>(textures_.size()) || count <= 0) {
    return;
  }
  auto it = local_catalog_.find(textures_[state.texture].surface_key);
  if (it == local_catalog_.end()) {
    return;
  }
  if (!vertices || count > 1024) {
    throw std::runtime_error("local_lights_observe: invalid vertex buffer");
  }
  VisualFloatScope guard;
  std::vector<mw34::effects::Point> points;
  points.reserve(static_cast<size_t>(count));
  for (int i = 0; i < count; ++i) {
    points.push_back(mw34::effects::reconstruct(
        vertices[i].sx, vertices[i].sy, vertices[i].sz, local_projection_,
        local_camera_));
  }
  local_observed_.observe(it->second, points, local_time_);
  ++local_observations_;
}

void local_lights_attach(vk::Scene &target) {
  target.effect_lights = {};
  if (!bridge_config_.effect_lights || !local_active_ || target.hud ||
      target.frontend_canvas) {
    return;
  }
  VisualFloatScope guard;
  std::vector<mw34::effects::Candidate> sources = local_native_;
  auto candidates = local_observed_.candidates(local_time_);
  sources.insert(sources.end(), headlight_candidates_.begin(), headlight_candidates_.end());
  // Keep within the ranker's 384-source cap without unsigned wraparound.
  const std::size_t room = sources.size() < 384 ? 384 - sources.size() : 0;
  const auto observed_count = std::min(candidates.size(), room);
  sources.insert(sources.end(), candidates.begin(), candidates.begin() + observed_count);
  fixture_refresh_sources(); // Revalidate lifetime/pose after all late producers.
  mw34::effects::Point eye = {local_camera_[3], local_camera_[7], local_camera_[11]};
  // At most48 fixtures can enter64 slots with the existing16-slot weapon
  // reserve. Preselect them with the same ranker; discarded fixtures cannot
  // enter the combined result. A full weapon frame leaves no fixture slots.
  if (candidates.size() < mw34::effects::capacity) {
    const auto fixtures = mw34::effects::rank_frame_lights(
        local_fixture_sources_.candidates(), eye, 64, 16);
    const auto fixture_room = sources.size() < 384 ? 384 - sources.size() : 0;
    const auto count = std::min(std::size_t(fixtures.params[0]), fixture_room);
    for (std::size_t index = 0; index < count; ++index) {
      mw34::effects::Candidate fixture{};
      fixture.source = (1ULL << 62) + index + 1;
      fixture.light = fixtures.lights[index];
      fixture.cone = fixtures.cones[index];
      sources.push_back(fixture);
    }
  }
  target.effect_lights = mw34::effects::rank_frame_lights(sources, eye, 64, 16);
  local_packet_peak_ =
      std::max(local_packet_peak_,
               static_cast<std::uint64_t>(target.effect_lights.params[0]));
}

void local_lights_report() {
  if (!bridge_config_.effect_lights) {
    return;
  }
  fprintf(
      stderr,
      "[LOCAL_LIGHTS] observations=%llu native_peak=%llu packet_peak=%llu\n",
      static_cast<unsigned long long>(local_observations_),
      static_cast<unsigned long long>(local_native_peak_),
      static_cast<unsigned long long>(local_packet_peak_));
  fprintf(stderr, "[NATIVE_FIXTURES] observations=%llu rejected=%llu vehicle_pending=%llu\n",
      (unsigned long long)fixture_observations_, (unsigned long long)fixture_rejections_,
      (unsigned long long)fixture_vehicle_pending_);
  fprintf(stderr, "[NATIVE_FIXTURE_LIFETIME] retained_peak=%llu expired=%llu evicted=%llu\n",
      (unsigned long long)fixture_retained_peak_,(unsigned long long)fixture_expired_,
      (unsigned long long)fixture_evictions_);
  if (bridge_config_.mech_headlights)
    fprintf(stderr, "[HEADLIGHTS] candidate_peak=%zu\n", headlight_peak_);
}
