"""Additive authored controls, derived from the frozen hardware fixture."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
def main():
 p=R/'tools/m4-capture-direct/controls_v3.cpp'
 t=p.read_text().replace('capture_direct_v3.hpp','capture_shared.hpp').replace('mw34::capture_direct','mw34::capture_shared')
 t=t.replace('for(auto name:{"a","b","c"}){operation(w,0,name,bytes.data(),mode==0?2:0,false);', 'unsigned ordinal=0;for(auto name:{"a","b","c"}){operation(w,0,name,bytes.data()+ordinal++,mode==0?2:0,false);')
 t=t.replace('r->parts.size()==(mode==1?2:3)', 'r->parts.size()==3')
 needle=' for(unsigned mode=0;mode<3;++mode){cd::Options o;if(mode==0)o.files_per_part=cd::max_files+1;'
 assert t.count(needle)==1
 extra=''' {cd::Options o;o.force_hash_key_collision=true;cd::Writer w(out/"collision",o);
  operation(w,0,"a/original",bytes.data(),bytes.size(),false);
  // Mutation after return cannot change the private append snapshot.
  bytes[255]^=0x80;operation(w,0,"b/one-byte-change",bytes.data(),bytes.size(),false);
  operation(w,0,"c/repeated-change",bytes.data(),bytes.size(),false);
  operation(w,0,"d/different-size",bytes.data(),bytes.size()-1,false);
  operation(w,0,"e/empty",nullptr,0,false);bytes[255]^=0x80;
  auto r=operation(w,2,"",nullptr,0,false);need(r&&r->logical_files==5&&r->payload_bytes==1023&&r->unique_blobs==4&&r->unique_payload_bytes==767,"Forced lookup-key collisions require full byte comparison and immutable input copies");}
'''
 t=t.replace(needle,extra+needle)
 out=H/'controls.cpp';assert not out.exists();out.write_text(t,encoding='utf-8',newline='\n')
 print('base_controls_sha256='+hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main()
