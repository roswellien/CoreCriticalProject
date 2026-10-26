// Pack-authored donor sockets adapt only the successful original muzzle output.
// Original firing, random spread, aim direction and guest return ABI stay intact.
OverrideMatrix chassis_socket_world(unsigned node) {
    auto result=override_identity();std::set<unsigned> seen;
    for(unsigned depth=0;node;++depth) {
        if(depth>=64||!seen.emplace(node).second||!readable(node,100))
            throw std::runtime_error("Chassis sockets: malformed source ancestry");
        const unsigned type=load(node+0x34);
        if(type==5) {
            const unsigned data=load(node+0x38);
            if(!readable(data,96))throw std::runtime_error("Chassis sockets: unreadable source transform");
            const auto local=(load(data)&8)?override_identity():override_matrix(data+0x30);
            result=override_product(local,result);
        }else if(type!=2&&type!=6)throw std::runtime_error("Chassis sockets: unsupported source transform type");
        const unsigned count=load(node+0x54);
        if(count>1)throw std::runtime_error("Chassis sockets: ambiguous source ancestry");
        if(!count)break;
        const unsigned parents=load(node+0x58);
        if(!readable(parents,4))throw std::runtime_error("Chassis sockets: unreadable parent");
        node=load(parents);
    }
    return result;
}
OverrideDonorInstance chassis_socket_pose(unsigned root,unsigned model) {
    auto& o=override_state();const auto key=std::make_pair(root,model);
    const auto previous=o.scope;auto cached=o.donor_poses.extract(key);
    o.scope.root=root;o.scope.model=model;
    try {
        auto result=override_donor_pose();
        o.donor_poses.erase(key);if(!cached.empty())o.donor_poses.insert(std::move(cached));
        o.scope=previous;return result;
    }catch(...) {
        o.donor_poses.erase(key);if(!cached.empty())o.donor_poses.insert(std::move(cached));
        o.scope=previous;throw;
    }
}
double chassis_socket_value(unsigned address) {
    if(!readable(address,4))throw std::runtime_error("Chassis sockets: unreadable nominal muzzle offset");
    unsigned bits=load(address);float value;std::memcpy(&value,&bits,4);
    if(!std::isfinite(value))throw std::runtime_error("Chassis sockets: nonfinite nominal muzzle offset");
    return value;
}
std::optional<std::array<double,3>> chassis_socket_delta(unsigned node,unsigned weapon,unsigned profile,bool mounted) {
    if(!node||!readable(node,100))return {};
    unsigned root=node;std::set<unsigned> seen;
    for(unsigned depth=0;;++depth) {
        if(!root||depth>=64||!seen.emplace(root).second)return {};
        if(additional_chassis.actor_roots.count(root))break;
        root=override_parent(root);
    }
    std::string name;
    if(profile) {
        if(!readable(profile,32))throw std::runtime_error("Chassis sockets: unreadable original firepoint profile");
        const unsigned text=load(profile);
        for(unsigned i=0;;++i) {
            if(i>=36||!readable(text+i,1))throw std::runtime_error("Chassis sockets: unterminated original firepoint name");
            const unsigned char c=runtime.memory().load<std::uint8_t>({text+i});if(!c)break;
            if(c<32||c>126)throw std::runtime_error("Chassis sockets: invalid original firepoint name");name+=char(c);
        }
    }else name=pose_name(node,36);
    if(name.size()!=11||name.compare(0,9,"firepoint")||name[9]<'0'||name[9]>'9'||name[10]<'0'||name[10]>'9')return {};
    const unsigned runtime_id=additional_chassis.actor_roots.at(root);
    const auto& records=mw34::chassis::configured_catalog();
    if(runtime_id<mw34::chassis::first_runtime_id||runtime_id-mw34::chassis::first_runtime_id>=records.size())
        throw std::runtime_error("Chassis sockets: unregistered actor identity");
    const auto& record=records[runtime_id-mw34::chassis::first_runtime_id];
    const auto socket=std::find_if(record.sockets.begin(),record.sockets.end(),[&](const auto& s){return s.node==name;});
    if(socket==record.sockets.end())return {};
    if(record.visual_template.empty())throw std::runtime_error("Chassis sockets: missing visual controller");
    unsigned model=~0U;
    for(unsigned i=0;i<override_models().size();++i) {
        const auto& candidate=override_models()[i];
        if(candidate.lod==0&&record.id==candidate.id&&candidate.resource&&record.resource==candidate.resource) {
            if(model!=~0U)throw std::runtime_error("Chassis sockets: ambiguous visual model");model=i;
        }
    }
    if(model==~0U)throw std::runtime_error("Chassis sockets: unavailable visual model");
    override_load_model(model);
    if(!override_state().donor_rigs.count(model))throw std::runtime_error("Chassis sockets: model has no donor rig");
    const auto pose=chassis_socket_pose(root,model);
    const auto& rig=override_state().donor_rigs.at(model);
    const auto bone=std::find_if(rig.bones.begin(),rig.bones.end(),[&](const auto& b){return b.name==socket->bone;});
    if(bone==rig.bones.end())throw std::runtime_error("Chassis sockets: missing donor socket bone");
    const auto donor_world=override_product(override_product(chassis_socket_world(root),mw34::donor::inverse(mw34::donor::axis())),pose.pose.world.at(size_t(bone-rig.bones.begin())));
    const auto original_world=chassis_socket_world(node);
    // 4B2530 retains the declared firepoint profile even though 41D510 maps
    // its anatomical mount to rhand/lhand. Preserve the original random term
    // by replacing only the nominal profile point, including fixed offsets.
    std::array<double,3> nominal{};
    if(!readable(weapon,0x90))throw std::runtime_error("Chassis sockets: unreadable weapon offsets");
    for(unsigned i=0;i<3;++i) {
        if(mounted&&profile)nominal[i]=chassis_socket_value(profile+0x14+4*i);
        if(!load(weapon+0x68)||!profile)nominal[i]+=chassis_socket_value(weapon+0x84+4*i);
    }
    std::array<double,3> delta{};
    for(unsigned axis=0;axis<3;++axis) {
        delta[axis]=donor_world[axis*4+3]-original_world[axis*4+3];
        for(unsigned i=0;i<3;++i)delta[axis]+=donor_world[axis*4+i]*socket->position[i]-original_world[axis*4+i]*nominal[i];
        if(!std::isfinite(delta[axis]))throw std::runtime_error("Chassis sockets: nonfinite socket translation");
    }
    return delta;
}
void* chassis_socket_body(State* s,unsigned target,void* p,Body body) {
    const unsigned weapon=state.gpr.rcx.dword,stack=state.gpr.rsp.dword;
    if(target!=0x4b36e0||!readable(weapon,0x98)||!readable(stack,20))return body(s,target,p);
    const unsigned output=load(stack+8);
    // Match the original 4B36E0->4ED650 node selection, including profile mounts.
    const unsigned mount=load(weapon+0x24),profile=load(weapon+0x80);
    const unsigned node=mount&&profile?(readable(mount,12)?load(mount+8):0):load(weapon+0x20);
    void* result=body(s,target,p);
    if(!(state.gpr.rax.dword&255))return result;
    const State returned=state;OverrideMxcsr fp;
    try {
        const auto delta=chassis_socket_delta(node,weapon,profile,mount!=0);
        if(delta) {
            if(!readable(output,12))throw std::runtime_error("Chassis sockets: unreadable original muzzle output");
            std::array<float,3> corrected{};
            for(unsigned i=0;i<3;++i) {
                unsigned bits=load(output+4*i);float value;std::memcpy(&value,&bits,4);
                corrected[i]=float(double(value)+(*delta)[i]);
                if(!std::isfinite(value)||!std::isfinite(corrected[i]))throw std::runtime_error("Chassis sockets: nonfinite original muzzle output");
            }
            for(unsigned i=0;i<3;++i){unsigned bits;std::memcpy(&bits,&corrected[i],4);store(output+4*i,bits);}
        }
        state=returned;return result;
    }catch(...){state=returned;throw;}
}
