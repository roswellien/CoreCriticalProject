// Included in the host adapter. All source hierarchy access is read-only.
template<class Reader> static mw34::donor::Rig override_read_donor(Reader&bytes){
 using namespace mw34::donor;Rig rig;unsigned bones,refs,flags;bytes(&bones,4);bytes(&refs,4);bytes(&flags,4);
 if(!bones||bones>256||!refs||refs>128||flags>3)throw std::runtime_error("Visual retarget: invalid rig counts/flags");rig.ground_reference=(flags&1)!=0;rig.hinge_axes=(flags&2)!=0;
 bytes(&rig.hip_drop,8);bytes(rig.walk_x.data(),16);bytes(rig.walk_z.data(),16);
 for(double v:{rig.hip_drop,rig.walk_x[0],rig.walk_x[1],rig.walk_z[0],rig.walk_z[1]})if(!std::isfinite(v))throw std::runtime_error("Visual retarget: nonfinite gait metadata");
 if(rig.hip_drop<0||rig.hip_drop>10)throw std::runtime_error("Visual retarget: invalid hip offset");
 auto name=[&](){char n[32];bytes(n,32);if(n[31])throw std::runtime_error("Visual retarget: unterminated name");return std::string(n);};
 auto matrix=[&](){Mat m;bytes(m.data(),128);for(double v:m)if(!std::isfinite(v))throw std::runtime_error("Visual retarget: nonfinite rest matrix");if(m[12]!=0||m[13]!=0||m[14]!=0||m[15]!=1)throw std::runtime_error("Visual retarget: nonaffine rest matrix");inverse(m);return m;};
 std::set<std::string>names;
 for(unsigned i=0;i<bones;++i){Bone b;b.name=name();b.control=name();bytes(&b.parent,4);b.rest=matrix();if(b.name.empty()||!names.emplace(b.name).second||b.parent< -1||b.parent>=int(i))throw std::runtime_error("Visual retarget: invalid bone hierarchy");rig.bones.push_back(std::move(b));}
 for(unsigned i=0;i<refs;++i){auto n=name();auto m=matrix();if(n.empty()||!rig.reference.emplace(n,m).second)throw std::runtime_error("Visual retarget: duplicate source reference");}
 for(const char*n:{"hip","torso","larm","rarm","lfoot","rfoot","lthigh","rthigh","lcalf","rcalf"})if(!rig.reference.count(n))throw std::runtime_error("Visual retarget: missing original reference");
 for(const char*n:{"Pelvis","Torso_Twist","Upperarm_Left","Upperarm_Right","Forearm_Left","Forearm_Right","Thigh_Left","Thigh_Right","Calf_Left","Calf_Right","Foot0_Left","Foot0_Right"})if(!names.count(n))throw std::runtime_error("Visual retarget: missing donor joint");
 for(const auto&b:rig.bones)if(!b.control.empty()&&!rig.reference.count(b.control))throw std::runtime_error("Visual retarget: unknown source binding");
 if(rig.hinge_axes)validate_hinge_metadata(rig);
 return rig;
}
OverrideDonorInstance&override_donor_pose(){
 auto&o=override_state();const auto key=std::make_pair(o.scope.root,o.scope.model);auto found=o.donor_poses.find(key);if(found!=o.donor_poses.end())return found->second;
 const auto&rig=o.donor_rigs.at(o.scope.model);OverrideDonorInstance instance;std::map<unsigned,OverrideMatrix>world;world.emplace(o.scope.root,override_identity());
 std::vector<unsigned>queue{o.scope.root};std::set<unsigned>seen;const auto a=mw34::donor::axis();const auto ai=mw34::donor::inverse(a);std::map<std::string,OverrideMatrix>display;
 for(size_t at=0;at<queue.size();++at){const unsigned node=queue[at];if(at>=256||!seen.emplace(node).second||!readable(node,100))throw std::runtime_error("Visual retarget: malformed live hierarchy");
  auto m=world.at(node);const auto name=pose_name(node,36);if(rig.reference.count(name)){if(!instance.raw.emplace(name,m).second)throw std::runtime_error("Visual retarget: duplicate live control");display.emplace(name,override_product(override_product(a,m),ai));}
  const unsigned count=load(node+0x5c),children=load(node+0x60);if(count>64||(count&&!readable(children,count*4)))throw std::runtime_error("Visual retarget: unreadable live children");
  for(unsigned i=0;i<count;++i){const unsigned child=load(children+i*4);if(!readable(child,100)||load(child+0x34)!=5)throw std::runtime_error("Visual retarget: unsupported live control");const unsigned data=load(child+0x38);if(!readable(data,96))throw std::runtime_error("Visual retarget: unreadable live transform");
   auto local=(load(data)&8)?override_identity():override_matrix(data+0x30);if(!world.emplace(child,override_product(m,local)).second)throw std::runtime_error("Visual retarget: shared live child");queue.push_back(child);
  }
 }
 // Missing detached controls are reconstructed from their original parent frame
 // for the visual solver only. Their geometry remains hidden by original activity.
 for(const auto&[name,reference]:rig.reference)if(!display.count(name)){
  const std::string side=name.rfind("l",0)==0?"l":name.rfind("r",0)==0?"r":"";
  std::string ancestor="torso";
  if(!side.empty()){
   if(name.rfind(side+"toe",0)==0)ancestor=side+"foot";
   else if(name==side+"hand")ancestor=side+"arm";
   else if(name==side+"foot")ancestor=side+"calf";
   else if(name==side+"calf")ancestor=side+"thigh";
   else if(name==side+"thigh")ancestor="hip";
  }
  if(!display.count(ancestor))ancestor="torso";if(!display.count(ancestor))throw std::runtime_error("Visual retarget: missing live torso");
  display.emplace(name,override_product(override_product(display.at(ancestor),mw34::donor::inverse(rig.reference.at(ancestor))),reference));
 }
 instance.gait=mw34::donor::locomotion(rig,display);instance.pose=mw34::donor::retarget(rig,display,instance.gait);
 if(instance.pose.reach_clamps&&o.retarget_clamp_roots.emplace(key).second){o.log<<"{\"event\":\"visual_reach_clamped\",\"root\":"<<o.scope.root<<",\"model\":\""<<override_models[o.scope.model].id<<"\",\"joints\":"<<instance.pose.reach_clamps<<",\"scope\":\"visual length-preserving reach limit; gameplay unchanged\"}\n";o.log.flush();}
 return o.donor_poses.emplace(key,std::move(instance)).first->second;
}
