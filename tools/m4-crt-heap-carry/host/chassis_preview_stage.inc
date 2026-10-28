// Additional-mech framing uses immutable donor rest geometry. A rotating
// screen-space AABB must never determine the presentation scale.
std::map<unsigned,mw34::mechpreview::Framing> chassis_preview_frames;
void chassis_preview_camera(unsigned model,OverrideMatrix& root_camera,
                            double near_scale,double& scale_x,double& scale_y,
                            double& center_x,double& center_y,double near_clip) {
    auto& state_=override_state();
    if(!frontend_on()||!override_models().at(model).resource)return;
    const auto rig=state_.donor_rigs.find(model);
    if(rig==state_.donor_rigs.end())
        throw std::runtime_error("Additional mech preview: donor controller unavailable");
    auto found=chassis_preview_frames.find(model);
    if(found==chassis_preview_frames.end()) {
        std::array<double,3> low{},high{};bool point{};
        for(const auto& batch:state_.batches)if(batch.model==model) {
            for(size_t i=0;i<batch.vertices.size();++i) {
                const auto bone=batch.vertex_bones.empty()?batch.donor_bone:batch.vertex_bones.at(i);
                const auto& matrix=rig->second.bones.at(bone).rest;
                const auto& vertex=batch.vertices[i];
                const std::array<double,3> local{vertex.x,vertex.y,vertex.z};
                for(unsigned row=0;row<3;++row) {
                    double value=matrix[row*4+3];
                    for(unsigned axis=0;axis<3;++axis)value+=matrix[row*4+axis]*local[axis];
                    if(!point)low[row]=high[row]=value;
                    else {low[row]=std::min(low[row],value);high[row]=std::max(high[row],value);}
                }
                point=true;
            }
        }
        if(!point)throw std::runtime_error("Additional mech preview: geometry unavailable");
        found=chassis_preview_frames.emplace(model,mw34::mechpreview::framing(low,high)).first;
    }
    const auto camera=mw34::mechpreview::camera(found->second,root_camera,near_scale,scale_x,scale_y,near_clip);
    root_camera=camera.matrix;scale_x=camera.projection[1];scale_y=camera.projection[2];
    center_x=camera.projection[3];center_y=camera.projection[4];
}
