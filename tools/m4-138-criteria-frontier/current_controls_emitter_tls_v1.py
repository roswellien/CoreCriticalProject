"""Exact source-declared sixteen-byte Emitter in current owning TLS24 section."""
NAME='?emitter@?A0xCA9AC4E1@m4_mfc1168_connected@mw34@@3UEmitter@?A0xCA9AC4E1@12@A'
def prove(sym,physical_symbols,physical_sections,source):
 assert 'struct Emitter {Sink sink{};void*opaque{};};'in source and 'thread_local Emitter emitter{};'in source
 assert sym['name']==NAME and sym['value']==8 and sym['type']==0 and sym['storage']==3 and sym['section']>0
 section=sym['section'];definitions=[s for s in physical_symbols.values()if s['section']==section]
 expected=[('.tls$',0,0,3),('?current@Impl@Component@m4_mfc1168_connected@mw34@@2PEAU1234@EA',0,0,2),(NAME,8,0,3)]
 assert [(s['name'],s['value'],s['type'],s['storage'])for s in definitions]==expected and sym==definitions[2]
 assert physical_sections[section]['bytes']==bytes(24)and not physical_sections[section]['relocations']
 return dict(section=section,whole_zero_bytes=24,current_pointer_offset=0,emitter_offset=8,emitter_bytes=16,sink_offset=8,opaque_offset=16,exact_symbol=NAME)
