"""Pure finite source table/resource/ABI controls; no DLL/native worker run."""
from pathlib import Path
import collections,hashlib,json,struct,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main():
 out=R/'reports/m4-loader-message-review/bounded-controls-r1';need(not out.exists(),'Fresh bounded controls');out.mkdir();controls=[];pins={}
 def pin(p,h=None):p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical input');pins[str(p)]=v;return p
 def okay(label,fn):fn();controls.append(dict(name=label,passed=True))
 def refused(label,fn):
  try:fn()
  except ValueError:controls.append(dict(name=label,refused=True));return
  raise AssertionError('Adverse accepted '+label)
 root=R/'reports/m4-loader-message-review/physical-r4';proof=json.loads(pin(root/'report.json','138452ce77ef212ca239499794e0aa9e4a6034a64361a70fc71b0896205959e4').read_bytes());source=json.loads(pin(root/'current-name-id-table.json').read_bytes());rows=source['rows'];need(len(rows)==1577,'Authentic current whole table')
 def table_valid(rows):need(len(rows)==1577 and len({r['name']for r in rows})==1577 and len({r['id']for r in rows})==1577,'Exact current finite unique table')
 okay('all1577-unique-source-names-and-IDs',lambda:table_valid(rows))
 actual=rows.copy();moves=0
 for i in range(1,len(actual)):
  item=actual[i];j=i
  while j and item['name'].encode('ascii')<actual[j-1]['name'].encode('ascii'):actual[j]=actual[j-1];j-=1;moves+=1
  actual[j]=item
 expected=pin(root/'current-sorted-table-design.bin').read_bytes();endpoint=b''.join(struct.pack('<II',r['name_pointer'],r['id'])for r in actual)
 okay('independent-insertion-endpoint-whole12616B',lambda:need(endpoint==expected,'Complete sorted unique permutation'))
 okay('whole-source-name-pointer-ID-association-retained',lambda:need(collections.Counter((r['name_pointer'],r['id'])for r in rows)==collections.Counter((r['name_pointer'],r['id'])for r in actual),'No dropped/invented pair'))
 staged=json.loads(pin(root/'staged-name-id-table.json').read_bytes());refused('staged1540-is-not-current1577',lambda:table_valid(staged['rows']))
 bad=[dict(r)for r in rows];bad[1]['name']=bad[0]['name'];refused('duplicate-name-frontier-refused',lambda:table_valid(bad));bad=[dict(r)for r in rows];bad[1]['id']=bad[0]['id'];refused('duplicate-ID-frontier-refused',lambda:table_valid(bad))
 res=json.loads(pin(root/'current-resources.json').read_bytes())[0];need(res['path']==[11,1,1033]and res['message_count']==1577,'Exact current whole typed resource');ids={id for b in res['message_blocks']for id in range(b['low'],b['high']+1)};okay('all-name-IDs-belong-to-current-message-resource',lambda:need(ids=={r['id']for r in rows},'All-and-only named resource IDs'))
 payload=pin(res['payload_path'],res['sha256']).read_bytes();refused('same-size-resource-mutation-refused',lambda:need(hashlib.sha256(bytes([payload[0]^1])+payload[1:]).hexdigest()==res['sha256'],'Whole raw payload identity'))
 for label,pc,raw in [('literal-user-entry-calls-sort',0x10001710,'e8ebf8ffff'),('CRT-actual128-allocation-immediate',0x10001a8d,'6880000000'),('actual-source-initializer-range-end',0x10001ab5,'6804300010'),('actual-source-initializer-range-begin',0x10001aba,'6800300010')]:
  cfg=json.loads(pin(root/'current-physical-CFG.json').read_bytes());d={r['pc']:r for r in cfg['rows']};okay(label,lambda pc=pc,raw=raw:need(d[pc]['bytes']==raw,'Every exact physical source instruction'))
 for p in [Path(__file__),Path(sys.executable),Path(__file__).with_name('abi_witness.cpp'),Path(__file__).with_name('native_loader_provider.cpp'),Path(__file__).with_name('native_provider.cpp'),Path(__file__).with_name('inspect_message.py'),Path(__file__).with_name('inspect_message_v2.py'),Path(__file__).with_name('inspect_message_v3.py'),Path(__file__).with_name('inspect_message_v4.py')]:pin(p)
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Pure finite name-table/typed whole-resource/source-literal/negative provenance controls only; original quicksort instruction equivalence and DLL execution not tested',controls=controls,source_pairs=1577,whole_sorted_endpoint_bytes=12616,independent_endpoint_moves=moves,source_literal_algorithm_executed=False,native_DLL_executed=False,native_provider_API_executed=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(q),controls=len(controls),moves=moves)))
if __name__=='__main__':main()
