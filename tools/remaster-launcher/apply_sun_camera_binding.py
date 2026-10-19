"""Authenticate camera words at the original renderer activation, read-only.

Apply to a private host. Retains exact checks; no tolerance, guest writes, or
original-body substitution. Current camera nodes may change after activation.
"""
from pathlib import Path
import argparse
import shutil

DECLARATIONS = '''
mw34::sun::CameraBinding sun_view_binding;
mw34::sun::CameraBinding::Words sun_view_words(unsigned address){
 if(!address||!readable(address,48))throw std::runtime_error("Sun camera activation is unreadable");
 mw34::sun::CameraBinding::Words words{};for(unsigned i=0;i<12;++i)words[i]=load(address+i*4);return words;
}
bool sun_view_capture_enabled(){
 static const bool enabled=[]{SunCaptureFp preserve;return mw34::sun::settings().enabled;}();return enabled;
}
'''
HOOK = '''  if(target==0x520b00&&sun_view_capture_enabled()){
   const unsigned source=state.gpr.rcx.dword;
   mw34::sun::CameraBinding::Words words{};
   {SunCaptureFp preserve;words=sun_view_words(source);sun_view_binding.valid=false;}
   void*r=remaster_body_inner(s,target,p,body);
   {SunCaptureFp preserve;sun_view_binding.capture(source,words,sun_view_words(0x73fc00),sun_view_words(0x73fbc0));}
   return r;
  }
'''
OLD = ''' auto expected=override_matrix(data+0x44);
 for(unsigned row=0;row<3;++row){expected[row*4+1]=-expected[row*4+1];expected[row*4+2]=-expected[row*4+2];}
 matrix=override_matrix(0x73fc00);
 for(unsigned i=0;i<12;++i)if(matrix[i]!=expected[i])throw std::runtime_error("Sun camera binding and renderer basis disagree");'''
NEW = ''' // 73FC00 is also scratch for original Euler-matrix construction.
 // Authenticate the active inverse view; use the exact camera words captured
 // when original 520B00 produced that view, not later scratch contents.
 if(!sun_view_binding.owns(data+0x44))return false; // Original temporary effect camera.
 sun_view_binding.validate(sun_view_words(0x73fbc0));
 matrix=sun_view_binding.matrix();'''


def apply(host):
    host = Path(host)
    stage = host/'sun_lighting_stage.inc';lighting = stage.read_text()
    adapter = host/'mfc_stage.hpp';text = adapter.read_text()
    lighting=lighting.replace('The unchanged camera-to-world copy is at 73FC00;',
                              'The camera activation copy is at 73FC00;')
    # Upgrade the retained first diagnostic implementation without a guess at
    # unrelated host versions. Original build and failed controls stay local.
    lighting=lighting.replace(' sun_view_binding.validate(data+0x44,sun_view_words(0x73fc00));\n matrix=override_matrix(0x73fc00);', NEW)
    lighting=lighting.replace('sun_view_binding.validate(data+0x44,sun_view_words(0x73fbc0));', 'sun_view_binding.validate(sun_view_words(0x73fbc0));')
    if 'sun_view_binding.owns(' not in lighting:
        lighting=lighting.replace(' sun_view_binding.validate(sun_view_words(0x73fbc0));\n matrix=sun_view_binding.matrix();', NEW)
    text=text.replace('sun_view_binding.capture(source,words,sun_view_words(0x73fc00));',
                      'sun_view_binding.capture(source,words,sun_view_words(0x73fc00),sun_view_words(0x73fbc0));')
    if 'sun_view_binding.validate(' not in lighting:
        if lighting.count(OLD)!=1:raise ValueError('Unreviewed sun camera contract')
        lighting=lighting.replace(OLD, NEW)
        anchor='bool sun_camera_world(OverrideMatrix& matrix) {'
        if lighting.count(anchor)!=1:raise ValueError('Missing camera adapter')
        lighting=lighting.replace(anchor, DECLARATIONS+'\n'+anchor)
    if '#include "sun_camera_binding.hpp"' not in text:
        anchor='#include "menu_wave.hpp"'
        if text.count(anchor)!=1:raise ValueError('Missing shared host include anchor')
        text=text.replace(anchor, anchor+'\n#include "sun_camera_binding.hpp"')
    if 'sun_view_binding.capture(' not in text:
        anchor=' void*lighting_body(State*s,unsigned target,void*p,Body body){\n'
        if text.count(anchor)!=1:raise ValueError('Missing original-body wrapper anchor')
        text=text.replace(anchor, anchor+HOOK)
    shutil.copyfile(Path(__file__).resolve().parents[2]/'runtime/graphics/sun_camera_binding.hpp',host/'sun_camera_binding.hpp')
    stage.write_text(lighting);adapter.write_text(text)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source',type=Path)
    args=parser.parse_args();apply(args.host_source.resolve(strict=True))
