"""Add two ancestor-frame visual translations without changing legacy payloads.

BWMESH5 extends BWMESH3 with one additional bounded frame/offset. A shoulder
correction follows the torso while the donor elbow spacing follows its upper
arm. Required when both pivots differ from the original skeleton. Guest poses
and weapon origins remain read-only.
"""
from pathlib import Path
import argparse

def apply(path):
    original=path.read_text();s=original
    def edit(old,new):
        nonlocal s
        if s.count(old)!=1:raise RuntimeError('Unsupported adapter source at '+old[:90])
        s=s.replace(old,new,1)
    edit('int skin_d_texture{-1};};',
         'int skin_d_texture{-1};std::string joint_frame;std::array<float,3>joint_offset{};};')
    edit('const bool placement=std::memcmp(magic,"BWMESH3\\0",8)==0;const bool component_visibility=donor||placement||',
         'const bool layered=std::memcmp(magic,"BWMESH5\\0",8)==0;const bool placement=layered||std::memcmp(magic,"BWMESH3\\0",8)==0;const bool component_visibility=donor||placement||')
    edit('   unsigned donor_bone=~0U;if(donor)', '''   char joint_name[32]{};std::array<float,3>joint_offset{};
   if(layered){bytes(joint_name,32);bytes(joint_offset.data(),12);if(joint_name[31])throw std::runtime_error("Replacement models: invalid joint frame");
    for(float value:joint_offset)if(!std::isfinite(value))throw std::runtime_error("Replacement models: nonfinite joint offset");
    if(!joint_name[0]){for(float value:joint_offset)if(value!=0)throw std::runtime_error("Replacement models: joint offset without frame");}
    else{bool found=false;for(size_t r=0;r<model.count;++r)if(std::string(joint_name)==model.roster[r].owner)found=true;if(!found)throw std::runtime_error("Replacement models: unknown joint frame");}}
   unsigned donor_bone=~0U;if(donor)''')
    edit('batch.donor_bone=donor_bone;batch.vertices.resize(size);',
         'batch.donor_bone=donor_bone;batch.joint_frame=joint_name;batch.joint_offset=joint_offset;batch.vertices.resize(size);')
    anchor='  D3DCmd draw'
    # Keep the same source-controlled camera orientation; only translation changes.
    idx=s.index(anchor,s.index('void override_emit()'))
    s=s[:idx]+'''  if(!batch.joint_frame.empty()){
   auto found=placement_frames.find(batch.joint_frame);if(found==placement_frames.end())found=placement_frames.emplace(batch.joint_frame,override_placement_frame_camera(batch.joint_frame,control_to_camera)).first;
   for(unsigned row=0;row<3;++row)for(unsigned col=0;col<3;++col)batch_to_camera[row*4+3]+=found->second[row*4+col]*batch.joint_offset[col];
  }
'''+s[idx:]
    if s==original:raise RuntimeError('No adapter changes')
    path.write_text(s)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('adapter',type=Path);apply(parser.parse_args().adapter)
