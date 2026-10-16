// Match complete, source-defined arm-loss alternatives. Unknown additions,
// partial deletions and changed surviving mesh signatures still decline.
// Stump geometry remains on the original drawing path.
bool override_arm_damage_match(const OverrideModel&model,
 const std::map<std::string,unsigned>&meshes,
 const std::map<std::string,unsigned>&mesh_nodes,unsigned&damage_mask){
 if(!meshes.count("rarm_stub01")&&!meshes.count("larm_stub01"))return false;
 std::map<std::string,unsigned>expected;
 for(size_t i=0;i<model.count;++i)expected.emplace(model.roster[i].name,model.roster[i].vertices);
 damage_mask=0;
 for(const auto&plan:override_arm_damage_plans){
  if(model.id!=std::string(plan.model)||model.lod!=plan.lod)continue;
  const auto stub=meshes.find(plan.stub);if(stub==meshes.end())continue;
  if(stub->second!=plan.vertices)return false;
  const auto instance=mesh_nodes.find(plan.stub);if(instance==mesh_nodes.end())return false;
  // Original 461D80 renames a meshless stub root to the lost limb name
  // and attaches it to the old parent. Do not admit the prototype elsewhere.
  const unsigned arm=override_parent(instance->second);
  if(!arm||pose_name(arm,36)!=std::string(plan.stub).substr(0,4)||load(arm+0x3c))return false;
  if(load(arm+0x5c)!=1||!readable(load(arm+0x60),4)||load(load(arm+0x60))!=instance->second)return false;
  const unsigned parent=override_parent(arm);
  if(!parent||pose_name(parent,36)!=plan.parent)return false;
  const unsigned mesh=load(instance->second+0x3c);
  if(!readable(mesh,0x3c)||load(mesh+0x10)!=19||load(mesh+0x18)!=0)return false;
  const unsigned vertices=load(mesh+0x38);
  if(!readable(vertices,plan.vertices*12))return false;
  std::uint64_t hash=0xcbf29ce484222325ULL;
  for(unsigned i=0;i<plan.vertices*3;++i){const unsigned word=load(vertices+i*4);
   for(unsigned shift=0;shift<32;shift+=8){hash^=(word>>shift)&255U;hash*=0x100000001b3ULL;}}
  if(hash!=plan.vertex_hash)return false;
  for(unsigned i=0;i<plan.count;++i){
   if(meshes.count(plan.removed[i])||expected.erase(plan.removed[i])!=1)return false;
  }
  if(!expected.emplace(plan.stub,plan.vertices).second)return false;
  damage_mask|=plan.stub[0]=='r'?1U:2U;
 }
 return damage_mask&&expected==meshes;
}
