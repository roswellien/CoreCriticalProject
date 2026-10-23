"""Prepared ROOT-only pure representation controls, no CPU/model/reader."""
from pathlib import Path
import importlib.util,copy
def main():
 p=Path(__file__).with_name('native_journal_sequence_v1.py');s=importlib.util.spec_from_file_location('J',p);J=importlib.util.module_from_spec(s);s.loader.exec_module(J)
 a=[(0x4103f0,0x200017fc,0x4103f5,4,1),(0x78001306,0x78035004,1,4,0)];b=[list(v)for v in a];assert J.equal(a,b)and J.equal(tuple(a),tuple(tuple(v)for v in b));names=[]
 def reject(name,change):
  x,y=copy.deepcopy((a,b));change(x,y)
  try:accepted=J.equal(x,y)
  except ValueError:accepted=False
  if accepted:raise AssertionError('Accepted adverse '+name)
  names.append(name)
 for i,name in enumerate(('PC','address','value','width','write')):
  reject('changed-'+name,lambda x,y,i=i:y[0].__setitem__(i,y[0][i]^1))
  reject('actual-Boolean-'+name,lambda x,y,i=i:x.__setitem__(0,tuple(True if j==i else v for j,v in enumerate(x[0]))))
  reject('carried-Boolean-'+name,lambda x,y,i=i:y[0].__setitem__(i,True))
 reject('first-order',lambda x,y:y.reverse());reject('whole-length',lambda x,y:y.pop());reject('extra-row',lambda x,y:y.append(list(y[0])));reject('short-row',lambda x,y:y[0].pop());reject('long-row',lambda x,y:y[0].append(0));reject('row-dict',lambda x,y:y.__setitem__(0,dict(enumerate(y[0]))));reject('negative-address',lambda x,y:y[0].__setitem__(1,-1));reject('overflow-PC',lambda x,y:y[0].__setitem__(0,0x100000000));reject('overflow-value',lambda x,y:y[0].__setitem__(2,0x10000000000000000));reject('invalid-width',lambda x,y:y[0].__setitem__(3,3));reject('invalid-write',lambda x,y:y[0].__setitem__(4,2))
 try:J.equal(iter(a),b)
 except ValueError:names.append('iterator-refused')
 else:raise AssertionError('Iterator admitted')
 print(dict(passed=True,adverse_controls=len(names),names=names,reader_opened=False,CPU_model_executed=False))
if __name__=='__main__':main()
