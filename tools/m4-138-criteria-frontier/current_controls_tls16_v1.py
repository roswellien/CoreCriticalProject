"""Exact initialized two-owner TLS section; not a general sixteen-byte domain."""
def prove(sym,sections,physical_symbols,physical_sections):
 assert sections==physical_sections,'Complete current owning COFF section table'
 section=sym['section'];assert section>0
 definitions=[s for s in physical_symbols.values()if s['section']==section]
 expected=[('.tls$',0,0,3),('?observation@m4_mixed@mw34@@3PEAUNative@12@EA',0,0,2),('?injection@context_control@@3PEAUInjection@1@EA',8,0,3)]
 assert [(s['name'],s['value'],s['type'],s['storage'])for s in definitions]==expected
 assert sym in definitions[1:],'Exact physical owning symbol, including storage class'
 storage=sections[section]['bytes'];assert storage==bytes(16)and sections[section]['relocations']==[]
 assert sym['value']in(0,8)and storage[sym['value']:sym['value']+8]==bytes(8)
 return dict(section=section,whole_zero_bytes=16,owners=[dict(name=s['name'],offset=s['value'],bytes=8,storage_class=s['storage'])for s in definitions[1:]])
