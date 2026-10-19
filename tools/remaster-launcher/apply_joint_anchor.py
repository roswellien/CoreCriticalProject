"""Add optional visual pivot anchoring to the BWMESH5 adapter.

BWMESH6 adds a named live ancestor control and its fixed position in the
existing placement frame. This removes source animation's compensating pivot
translations from a replacement assembly, retaining source rotations and all
guest simulation state. Legacy formats and unanchored batches are unchanged.
"""
from pathlib import Path
import argparse


def apply(path):
    original = path.read_text()
    source = original

    def edit(old, new):
        nonlocal source
        if source.count(old) != 1:
            raise RuntimeError('Unsupported adapter source at ' + old[:90])
        source = source.replace(old, new, 1)

    edit('std::array<float,3>joint_offset{};};',
         'std::array<float,3>joint_offset{};std::string anchor_control;std::array<float,3>anchor_position{};};')
    edit('const bool layered=std::memcmp(magic,"BWMESH5\\0",8)==0;',
         'const bool anchored=std::memcmp(magic,"BWMESH6\\0",8)==0;const bool layered=anchored||std::memcmp(magic,"BWMESH5\\0",8)==0;')
    edit('   unsigned donor_bone=~0U;if(donor)', '''   char anchor_name[32]{};std::array<float,3>anchor_position{};
   if(anchored){bytes(anchor_name,32);bytes(anchor_position.data(),12);if(anchor_name[31])throw std::runtime_error("Replacement models: invalid anchor control");
    for(float value:anchor_position)if(!std::isfinite(value))throw std::runtime_error("Replacement models: nonfinite anchor position");
    if(!anchor_name[0]){for(float value:anchor_position)if(value!=0)throw std::runtime_error("Replacement models: anchor position without control");}
    else{if(!placement_name[0])throw std::runtime_error("Replacement models: anchor requires placement frame");bool found=false;for(size_t r=0;r<model.count;++r)if(std::string(anchor_name)==model.roster[r].owner)found=true;if(!found)throw std::runtime_error("Replacement models: unknown anchor control");}}
   unsigned donor_bone=~0U;if(donor)''')
    edit('batch.joint_offset=joint_offset;batch.vertices.resize(size);',
         'batch.joint_offset=joint_offset;batch.anchor_control=anchor_name;batch.anchor_position=anchor_position;batch.vertices.resize(size);')
    edit('  D3DCmd draw{D3DCmd::Draw,D3DPT_TRIANGLELIST', '''  if(!batch.anchor_control.empty()){
   auto anchor=placement_frames.find(batch.anchor_control);if(anchor==placement_frames.end())anchor=placement_frames.emplace(batch.anchor_control,override_placement_frame_camera(batch.anchor_control,control_to_camera)).first;
   const auto&parent=placement_frames.at(batch.placement_frame);
   for(unsigned row=0;row<3;++row){double desired=parent[row*4+3];for(unsigned col=0;col<3;++col)desired+=parent[row*4+col]*batch.anchor_position[col];batch_to_camera[row*4+3]+=desired-anchor->second[row*4+3];}
  }
  D3DCmd draw{D3DCmd::Draw,D3DPT_TRIANGLELIST''')
    path.write_text(source)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('adapter', type=Path)
    apply(parser.parse_args().adapter)
