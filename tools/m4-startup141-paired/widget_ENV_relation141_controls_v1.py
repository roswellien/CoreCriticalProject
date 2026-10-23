"""Prepared pure ROOT controls for conditional finite ENV relation, no capture/models."""
from pathlib import Path
import importlib.util,struct,copy
def main():
 def load(name):
  p=Path(__file__).with_name(name+'.py');s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 K=load('widget_ENV_relation141_v1');E=load('native_ENV28_v1');state=bytearray(3504);struct.pack_into('<H',state,2768,0x7f);state[2736+7]=state[2736+9]=1;struct.pack_into('<I',state,2776,0x4ce618);struct.pack_into('<H',state,2780,0x23);struct.pack_into('<H',state,2774,0x11d);struct.pack_into('<I',state,2784,0x60b494);struct.pack_into('<H',state,2788,0x2b);env=E.project(bytes(state));assert env==K.EXPECTED_EPOCH_ENV
 d=dict(sequence=0,phase=137,side='after',root=0x5a3c30,epoch_before_State=bytes(state),endpoint_State=bytes(state),original_ENV=env[:12]+bytes(14)+env[26:],native_ENV=env,project=E.project);assert K.compare(**d)['bytes_excluded']==0
 for phase in(137,138,139,140):
  for side in('before','after'):
   q=dict(d,phase=phase,side=side,root=K.ROOTS[phase],original_ENV=d['original_ENV']if K.active(0,phase,side)else env);assert K.compare(**q)['whole_ENV28_compared']
 names=[]
 def reject(name,f):
  q=copy.deepcopy(d);f(q)
  try:K.compare(**q)
  except (ValueError,AssertionError,struct.error):names.append(name);return
  raise AssertionError('Accepted adverse '+name)
 reject('wrong-sequence',lambda q:q.__setitem__('sequence',1));reject('wrong-pre-clear-side',lambda q:q.__setitem__('side','before'));reject('wrong-phase',lambda q:q.__setitem__('phase',136));reject('wrong-root',lambda q:q.__setitem__('root',0x5a3ff0));reject('Boolean-sequence',lambda q:q.__setitem__('sequence',False))
 for at in range(28):reject('original-byte-'+str(at),lambda q,at=at:q.__setitem__('original_ENV',q['original_ENV'][:at]+bytes([q['original_ENV'][at]^1])+q['original_ENV'][at+1:]))
 for at in range(12,26):reject('native-metadata-'+str(at),lambda q,at=at:q.__setitem__('native_ENV',q['native_ENV'][:at]+bytes([q['native_ENV'][at]^1])+q['native_ENV'][at+1:]))
 reject('native-State-projector-mismatch',lambda q:q.__setitem__('endpoint_State',bytes(3504)));reject('epoch-input-wrong-lastwriter',lambda q:q.__setitem__('epoch_before_State',bytes(3504)));reject('short-original-ENV',lambda q:q.__setitem__('original_ENV',q['original_ENV'][:-1]));reject('short-native-State',lambda q:q.__setitem__('endpoint_State',q['endpoint_State'][:-1]))
 print(dict(passed=True,adverse_controls=len(names),names=names,source_execution=False,reader_opened=False,bytes_excluded=0))
if __name__=='__main__':main()
