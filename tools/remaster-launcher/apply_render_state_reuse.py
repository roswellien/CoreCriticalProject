"""Reuse identical host render state without omitting any guest producer.

Keep every legacy state validation and alias update. Snapshot vectors remain
immutable; accepted sun-view payloads share ownership only on byte equality.
"""
import argparse
import hashlib
import json
from pathlib import Path

CONTRACTS = {
    'd3d_provider.inc': 'c40bf336d78b88136fe10b3bda365a588153ae589e107fbda89ca44cd57b275c',
    'sun_tl_capture_stage.inc': '85acfcc90d9683e6872068a5dd36d3e55f6dcdfe7824a234f0e7aa85d964d175',
}


def apply(host):
    files = {name: (host/name).read_text(encoding='utf-8') for name in CONTRACTS}
    for name, expected in CONTRACTS.items():
        if hashlib.sha256((host/name).read_bytes()).hexdigest() != expected:
            raise ValueError(name + ': render state contract changed; review required')
    def replace(name, old, new):
        if files[name].count(old) != 1:
            raise ValueError(name + ': render state anchor changed: ' + old)
        files[name] = files[name].replace(old,new)
    d='d3d_provider.inc'
    replace(d,'std::vector<unsigned>v(d.rs.begin(),d.rs.end());',
        'std::vector<unsigned>v;if(render_reuse_enabled()){v.reserve(531);v.insert(v.end(),d.rs.begin(),d.rs.end());}else v.assign(d.rs.begin(),d.rs.end());')
    # A deleted active viewport changes snapshot contents even when later
    # state setters are no-ops. Never retain that viewport in cached draws.
    replace(d,'if(dev->current==vsurf_root(arg(1)))dev->current=0;',
        'if(dev->current==vsurf_root(arg(1))){dev->current=0;++dev->epoch;}')
    assign='''const bool reuse=render_reuse_enabled();bool invalidated=false;
   // A repeated legacy state can still restore aliases changed through TSS.
   auto assign=[&](unsigned& cell,unsigned value){if(!reuse||cell!=value){cell=value;if(!invalidated){++dev->epoch;invalidated=true;}}};'''
    replace(d,'dev->rs[st]=v;++dev->epoch;',assign+'assign(dev->rs[st],v);')
    for old,new in (
        ('t0[D3DTSS_MAGFILTER]=v==D3DFILTER_LINEAR?D3DTFG_LINEAR:D3DTFG_POINT;',
         'assign(t0[D3DTSS_MAGFILTER],v==D3DFILTER_LINEAR?D3DTFG_LINEAR:D3DTFG_POINT);'),
        ('t0[D3DTSS_MINFILTER]=mn[v];t0[D3DTSS_MIPFILTER]=mp[v];',
         'assign(t0[D3DTSS_MINFILTER],mn[v]);assign(t0[D3DTSS_MIPFILTER],mp[v]);'),
        ('t0[D3DTSS_ADDRESSU]=t0[D3DTSS_ADDRESSV]=v;',
         'assign(t0[D3DTSS_ADDRESSV],v);assign(t0[D3DTSS_ADDRESSU],v);'),
        ('if(st==D3DRENDERSTATE_TEXTUREADDRESSU)t0[D3DTSS_ADDRESSU]=v;',
         'if(st==D3DRENDERSTATE_TEXTUREADDRESSU)assign(t0[D3DTSS_ADDRESSU],v);'),
        ('if(st==D3DRENDERSTATE_TEXTUREADDRESSV)t0[D3DTSS_ADDRESSV]=v;',
         'if(st==D3DRENDERSTATE_TEXTUREADDRESSV)assign(t0[D3DTSS_ADDRESSV],v);'),
        ('dev->tss[stg][st]=arg(3);++dev->epoch;',assign+'assign(dev->tss[stg][st],arg(3));'),
        ('if(st==D3DTSS_ADDRESS)dev->tss[stg][D3DTSS_ADDRESSU]=dev->tss[stg][D3DTSS_ADDRESSV]=arg(3);',
         'if(st==D3DTSS_ADDRESS){assign(dev->tss[stg][D3DTSS_ADDRESSV],arg(3));assign(dev->tss[stg][D3DTSS_ADDRESSU],arg(3));}'),
    ):replace(d,old,new)
    sun='sun_tl_capture_stage.inc'
    for item,cache in [('light','sun_tl_values'),('view','sky_view_values')]:
        replace(sun,f'auto {item}=std::make_shared<mw34::sun::Tl>();',
            f'const bool reuse=render_reuse_enabled();mw34::sun::Tl pending{{}};std::shared_ptr<mw34::sun::Tl> owned;\n auto* {item}=reuse?&pending:(owned=std::make_shared<mw34::sun::Tl>()).get();')
        field='sun_tl' if item=='light' else 'sky_view'
        replace(sun,f'draw.{field}=std::move({item});',
            f'if(reuse)draw.{field}={cache}.capture(pending);else draw.{field}=std::move(owned);')
    path=host/'mfc_stage.hpp'
    text=path.read_text(encoding='utf-8')
    anchor='#include "body_dispatch.hpp"'
    member='#include "sun_tl_capture_stage.inc"'
    helper=host/'exact_shared_value.hpp'
    if text.count(anchor)!=1 or text.count(member)!=1 or helper.exists() or 'render_reuse_enabled' in text:
        raise ValueError('Render reuse member/include contract changed')
    text=text.replace(anchor,anchor+'\n#include "exact_shared_value.hpp"')
    text=text.replace(member,'''bool render_reuse_enabled(){
 static const bool enabled=[] {
  const char* value=std::getenv("MW34_RENDER_STATE_REUSE");
  if(!value||!*value||!std::strcmp(value,"0"))return false;
  if(!std::strcmp(value,"1"))return true;
  throw std::runtime_error("MW34_RENDER_STATE_REUSE must be 0 or 1");
 }();return enabled;
}
mw34::submission::ExactSharedValue<mw34::sun::Tl> sun_tl_values,sky_view_values;
'''+member)
    payload=(Path(__file__).parent/'native-overrides/exact_shared_value.hpp').read_bytes()
    # Do not partially modify a source tree whose required contracts changed.
    for name,data in files.items():(host/name).write_text(data,encoding='utf-8')
    path.write_text(text,encoding='utf-8');helper.write_bytes(payload)
    return dict(parent_contracts=CONTRACTS,helper_sha256=hashlib.sha256(payload).hexdigest())


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source',type=Path)
    print(json.dumps(apply(parser.parse_args().host_source.resolve(strict=True)),indent=2))
