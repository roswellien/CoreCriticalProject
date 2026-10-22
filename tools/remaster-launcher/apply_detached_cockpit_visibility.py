"""Hide identified original cockpit attachments in detached replacement views.

Patch the optional visual adapter in a frozen host source directory. Original
first-person rendering, chassis identity and guest scene state are preserved.
"""
from pathlib import Path
import argparse


def apply(path: Path) -> None:
    source = path.read_text()
    if "detached_attached_cockpit_suppressed" in source:
        raise RuntimeError("Detached cockpit visibility patch is already present")
    replacements = [
        ("unsigned skin{};};", "unsigned skin{};bool attached_cockpit{};};"),
        ("std::map<unsigned,mw34::donor::Rig>donor_rigs;", "std::set<std::pair<unsigned,std::string>>attached_cockpit_nodes;std::map<unsigned,mw34::donor::Rig>donor_rigs;"),
        ("if(attached){for(size_t i=0;i<cockpit.count;++i)meshes.erase(cockpit.meshes[i].name);break;}", "if(attached){for(size_t i=0;i<cockpit.count;++i){o.attached_cockpit_nodes.emplace(root,cockpit.meshes[i].name);meshes.erase(cockpit.meshes[i].name);}break;}"),
        ("const auto name=pose_name(node,36);if(!override_candidate_name(name))return previous;", """const auto name=pose_name(node,36);
 bool cockpit_candidate=false;
 if(photo_replay_detached_cam())for(const auto&roster:override_cockpit_rosters)for(size_t i=0;i<roster.count;++i)if(name==roster.meshes[i].name)cockpit_candidate=true;
 if(!override_candidate_name(name)&&!cockpit_candidate)return previous;"""),
        ("const int id=override_validate_root(root);if(id<0)return previous;const auto&model=override_models[id];", """const int id=override_validate_root(root);if(id<0)return previous;
 if(cockpit_candidate&&o.attached_cockpit_nodes.count({root,name})){
  o.scope={node,"",override_identity(),root,unsigned(id),0,true};
  if(o.announced_roots.emplace(root,0xfffd0000U).second){o.log<<"{\\"event\\":\\"detached_attached_cockpit_suppressed\\",\\"root\\":"<<root<<"}\\n";o.log.flush();}
  return previous;
 }
 const auto&model=override_models[id];"""),
        ("bool override_suppress_draw(){if(!override_enabled()||!override_state().scope.node)return false;", "bool override_suppress_draw(){if(!override_enabled()||!override_state().scope.node)return false;if(override_state().scope.attached_cockpit)return true;"),
        ("void override_emit(){if(!override_enabled())return;auto&o=override_state();", "void override_emit(){if(!override_enabled())return;auto&o=override_state();if(o.scope.attached_cockpit)return;"),
        ("override_state().validated_roots.clear();", "override_state().validated_roots.clear();override_state().attached_cockpit_nodes.clear();"),
    ]
    for old, new in replacements:
        if source.count(old) != 1:
            raise RuntimeError("Incompatible optional adapter source: " + old[:80])
        source = source.replace(old, new)
    path.write_text(source)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Frozen mesh_override_stage.inc")
    apply(parser.parse_args().source)
