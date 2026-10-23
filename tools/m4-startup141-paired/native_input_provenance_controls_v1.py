"""Prepared ROOT-only pure finite FS and prior-region provenance controls."""
from pathlib import Path
import importlib.util,struct,copy
def main():
 p=Path(__file__).with_name('native_input_provenance_v1.py');s=importlib.util.spec_from_file_location('P',p);P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
 state=bytearray(3504);struct.pack_into('<I',state,2168,0x7ffde000)
 comp=[[0x4103f0,0x200017fc,0x4103f5,4,1],[0x4103f5,0x20001800,0x410a80,4,0],[0x4c0310,0x200017f8,0,4,1],[0x4c0317,0x7ffde000,0xffffffff,4,0]]
 base=dict(root=0x4103f0,state=bytes(state),before_raw=b'',after_raw=b''.join(struct.pack('<IIQII',*v)for v in comp),carried=dict(root=0x4103f0,source_seed=False,AFTER_seed=False,whole_native_component_journals_compared=True,component_source_accesses=copy.deepcopy(comp),whole_literal_source_accesses=copy.deepcopy(comp),game_FS_observations=[dict(root=0x4103f0,PC=0x4c0317,kind=0,before_head=0xffffffff)]),contracts=dict(frames=[dict(read=0x4c0317)]))
 assert P.FS_cut(**base)['hex']=='ffffffff';assert P.prior_domains({0x20001000:4096},{0x20001000})['surviving_prior_regions']==0;names=[]
 def reject(n,mutation):
  d=copy.deepcopy(base);mutation(d)
  try:P.FS_cut(**d)
  except (ValueError,KeyError,struct.error):names.append(n);return
  raise AssertionError('Accepted adverse '+n)
 def component(d,index,offset,value):
  d['carried']['component_source_accesses'][index][offset]=value;d['after_raw']=b''.join(struct.pack('<IIQII',*v)for v in d['carried']['component_source_accesses'])
 reject('wrong-StateFS',lambda d:d.__setitem__('state',bytes(3504)));reject('short-State',lambda d:d.__setitem__('state',bytes(3503)));reject('wrong-root',lambda d:d.__setitem__('root',0x410440));reject('source-seed',lambda d:d['carried'].__setitem__('source_seed',True));reject('AFTER-seed',lambda d:d['carried'].__setitem__('AFTER_seed',True));reject('unproven-current-component',lambda d:d['carried'].__setitem__('whole_native_component_journals_compared',False));reject('broken-cumulative-prefix',lambda d:d.__setitem__('before_raw',bytes(24)));reject('incomplete-record',lambda d:d.__setitem__('after_raw',d['after_raw'][:-1]));reject('whole-actual-operand-mismatch',lambda d:d['carried']['component_source_accesses'][0].__setitem__(2,1))
 for offset,name,value in [(0,'read-PC',0x4c0577),(1,'address',0x7ffde001),(2,'value',0),(3,'width',1),(4,'write',1)]:reject('first-FS-'+name,lambda d,offset=offset,value=value:component(d,3,offset,value))
 reject('prior-unaligned-overlap',lambda d:(component(d,0,1,0x7ffddfff),component(d,0,3,2)));reject('prior-byte1-overlap',lambda d:(component(d,0,1,0x7ffde001),component(d,0,3,1)));reject('future-source-prefix',lambda d:d['carried']['whole_literal_source_accesses'][0].__setitem__(2,1));reject('undeclared-physical-FS-PC',lambda d:d.__setitem__('contracts',dict(frames=[])));reject('own-source-incoming-head',lambda d:d['carried']['game_FS_observations'][0].__setitem__('before_head',0));reject('wrong-observed-source-scope',lambda d:d['carried']['game_FS_observations'][0].__setitem__('root',0x410440))
 for label,prior,own in [('surviving-nonphase-input',{0x31000000:4096},{0x20001000}),('empty-region',{0x20001000:0},{0x20001000}),('Boolean-address',{True:4096},{True})]:
  try:P.prior_domains(prior,own)
  except ValueError:names.append(label)
  else:raise AssertionError('Accepted adverse '+label)
 print(dict(passed=True,adverse_controls=len(names),names=names,source_execution=False,reader_opened=False))
if __name__=='__main__':main()
