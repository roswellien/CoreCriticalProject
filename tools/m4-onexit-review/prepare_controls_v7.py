"""Independently attest the cleanup API after normal Session.finish."""
from pathlib import Path
H=Path(__file__).parent
def derive(name,old,changes):
 p=H/name;assert not p.exists();s=(H/old).read_text()
 for a,b in changes:assert s.count(a)>=1,(old,a);s=s.replace(a,b)
 p.write_text(s)
derive('fixture_hooks_v5.hpp','fixture_hooks_v4.hpp',[
 ('inline HANDLE pressure_heap{};','inline HANDLE pressure_heap{};\ninline mw34::m4_cmd_native::ApiIdentity cleanup_api_after;')])
derive('fixture_v6.inc','fixture_v5.inc',[
 ('fixture_hooks_v4.hpp','fixture_hooks_v5.hpp'),
 ('mw34_onexit_review::pressure_release();t.c->registry().finish();t.cleanup_ok=',
  'mw34_onexit_review::pressure_release();t.c->registry().finish();mw34_onexit_review::cleanup_api_after=mw34_onexit_review::pressure_identity("HeapDestroy",reinterpret_cast<std::uintptr_t>(&::HeapDestroy));t.cleanup_ok='),
 (' if(!retry&&!mw34_onexit_review::pressure_rows.empty()){',
  ''' if(!retry){
  const auto&a=mw34_onexit_review::cleanup_api_after;const auto id=prefix+"-cleanup-api-after";
  const std::array<std::uint64_t,11>v{a.target,a.named_target,a.owner,a.owner_named_target,a.region.base,a.region.bytes,a.region.allocation,a.region.state,a.region.type,a.region.protect,a.region.allocation_protect};
  w.append(id+".bin",v.data(),sizeof(v));w.append(id+"-module-path.bin",a.module_path.data(),a.module_path.size()*sizeof(wchar_t));w.append(id+"-module-sha.bin",a.module_sha.data(),a.module_sha.size());
 }
 if(!retry&&!mw34_onexit_review::pressure_rows.empty()){''')])
derive('build_controls_v7.py','build_controls_v6.py',[
 ('fixture_v5.inc','fixture_v6.inc'),('fixture_hooks_v4.hpp','fixture_hooks_v5.hpp'),
 ("pin(HERE/'prepare_controls_v6.py');","pin(HERE/'prepare_controls_v6.py');pin(HERE/'prepare_controls_v7.py');")])
derive('build_controls_v7.ps1','build_controls_v6.ps1',[('build_controls_v6.py','build_controls_v7.py')])
derive('run_controls_v3.py','run_controls_v2.py',[
 ("                        actual_after=e.identity(archive,stem+'after',pin)",
  '''                        if service=='destroy' and not any(archive.words(stem+'after.bin',11,'Q')):
                            need(archive.data(stem+'after-module-path.bin')==archive.data(stem+'after-module-sha.bin')==b'',
                                 'Retained normal candidate destroy-after observation is absent, not a fabricated identity')
                            actual_after=e.identity(archive,f'case-{selected}/first-cleanup-api-after',pin)
                        else:actual_after=e.identity(archive,stem+'after',pin)'''),
 ("                    research_pressure_scope=", "                    cleanup_API_identity_scope='Normal Binding.finish has no retained candidate destroy-after identity; independent fixture measures the same imported named physical target immediately after genuine Session.finish; one successful same-HANDLE HeapDestroy is separately authenticated',\n                    research_pressure_scope=")])
print('Derived fresh independent cleanup API observer and checker')
