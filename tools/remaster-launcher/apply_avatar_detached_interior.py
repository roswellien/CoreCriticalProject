"""Omit authenticated Avatar cockpit-interior meshes from detached views.

This display-only filter also works with original chassis geometry selected.
It requires the complete observed chassis plus interior roster; normal cockpit
views, the exterior head, gameplay traversal and unknown trees are untouched.
"""
from pathlib import Path
import argparse

HELPER = r'''
bool avatar_detached_interior_node(unsigned node){
 if(!photo_replay_detached_cam())return false;
 const auto name=pose_name(node,36);bool candidate=false;
 for(const auto&m:cockpit_avatar)if(name==m.name)candidate=true;
 if(!candidate)return false;
 unsigned root=0,current=node;
 for(unsigned depth_=0;current&&depth_<32;++depth_){if(pose_name(current,36)=="hip"){root=override_parent(current);break;}current=override_parent(current);}
 if(!root)return false;
 static unsigned frame=~0U;static std::map<unsigned,bool>cache;
 if(frame!=host.frames){frame=host.frames;cache.clear();}
 auto found=cache.find(root);if(found!=cache.end())return found->second;
 std::map<std::string,unsigned>meshes;std::vector<unsigned>todo{root};std::set<unsigned>seen;
 bool valid=true;
 for(size_t i=0;i<todo.size()&&valid;++i){
  if(i>=128||!seen.insert(todo[i]).second||!readable(todo[i],100)){valid=false;break;}
  const unsigned n=todo[i],count=load(n+0x5c),children=load(n+0x60);
  if(count>64||(count&&!readable(children,count*4))){valid=false;break;}
  for(unsigned j=0;j<count;++j)todo.push_back(load(children+4*j));
  const unsigned mesh=load(n+0x3c);
  if(mesh){if(!readable(mesh,24)||!meshes.emplace(pose_name(n,36),load(mesh+20)).second)valid=false;}
 }
 meshes.erase("left ski");meshes.erase("right ski");
 for(const auto&m:cockpit_avatar){auto f=meshes.find(m.name);if(f==meshes.end()||f->second!=m.vertices)valid=false;}
 bool chassis=false;
 auto match=[&](const auto&roster){
  if(meshes.size()!=roster.size()+cockpit_avatar.size())return false;
  for(const auto&m:roster){auto f=meshes.find(m.name);if(f==meshes.end()||f->second!=m.vertices)return false;}
  return true;
 };
 if(valid)chassis=match(override_avatar_meshes)||match(override_avatar_lod1_meshes);
 const bool hide=valid&&chassis;cache.emplace(root,hide);
 static std::set<unsigned>announced;
 if(hide&&announced.insert(root).second)std::cerr<<"Detached Avatar: authenticated interior omitted; original exterior retained\n";
 return hide;
}
'''

def apply(path: Path):
    source = path.read_text()
    hooks_path = path.with_name('mfc_stage.hpp')
    hooks = hooks_path.read_text()
    hook_gate = 'target==0x53f2e0&&override_enabled()'
    if hooks.count(hook_gate) != 1:
        raise RuntimeError('Unknown visual-adapter hook gate')
    if 'bool avatar_detached_interior_node' in source:
        raise RuntimeError('Avatar interior filter already installed')
    anchor = 'OverrideScope override_begin(unsigned node)'
    if source.count(anchor) != 1:
        raise RuntimeError('Unknown visual adapter entry')
    source = source.replace(anchor, HELPER + '\n' + anchor)
    gate = 'o.scope={};if(!override_enabled()||override_status_preview())return previous;'
    if source.count(gate) != 1:
        raise RuntimeError('Unknown visual adapter scope gate')
    source = source.replace(gate, 'o.scope={};if(!override_status_preview()&&avatar_detached_interior_node(node)){o.scope={node,"",override_identity(),0,0,0,true};return previous;}if(!override_enabled()||override_status_preview())return previous;')
    gate = 'bool override_suppress_draw(){if(!override_enabled()||!override_state().scope.node)return false;if(override_state().scope.attached_cockpit)return true;'
    if source.count(gate) != 1:
        raise RuntimeError('Unknown visual adapter draw gate')
    source = source.replace(gate, 'bool override_suppress_draw(){if(override_state().scope.node&&override_state().scope.attached_cockpit)return true;if(!override_enabled()||!override_state().scope.node)return false;')
    path.write_text(source)
    hooks_path.write_text(hooks.replace(hook_gate, 'target==0x53f2e0&&(override_enabled()||photo_replay_detached_cam())'))

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    apply(parser.parse_args().source)
