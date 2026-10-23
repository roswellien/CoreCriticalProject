"""Exact bounded current141 live ownership checks, inherited constructor gate separate."""
def need(v,m):
 if not v:raise ValueError(m)
def registry_summary(v):
 need(len(v)==32 and v[0]==1,'Exact current registry summary schema')
 need(v[10]<=98 and v[12]<=4096 and v[13]<=200000 and v[18]==200000,'Exact current private finite live98/API4096/source200000 resource domain')
 return v[10]
def locale_summary(v,cleaned=False):
 need(len(v)==32 and v[0]==1,'Exact current locale summary schema')
 need(v[14]<=98 and v[16]<=200000 and v[18]<=4096 and v[19]<=32,'Retained finite calls32/operands200000/API4096 and proved live98 bound')
 if cleaned:need(v[14:16]==(0,0),'Actual full corrected budget cleanup releases allocations and sections')
 return v[14]
def validate(data,seq,constructor_result):
 need(constructor_result['allocations']==6 and constructor_result['NULL_calls']==2,'Inherited exact six real constructor HeapAlloc births and two zero825 calls')
 prefix=f'sequence-{seq}/';peak=0
 for phase in range(141):
  for side in('before','after'):peak=max(peak,registry_summary(data.words(prefix+f'phase-{phase}-{side}-registry.bin',32,'Q')))
 for side in('selected','cleaned'):
  peak=max(peak,locale_summary(data.words(prefix+side+'/locale-summary.bin',32),side=='cleaned'))
 return dict(whole_phase_registry_endpoints=282,observed_endpoint_peak_live_allocations=peak,live_allocation_cap=98,extra_literal_constructor_births=6,other_resource_caps_unchanged=True,all_private_resources_cleaned=True)
