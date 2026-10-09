"""Correlate literal source CFG to preserved pre/optimized instruction markers."""
import hashlib
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import unique_object,normalized,verify_manifest
from paths import publish_bytes
def need(v,m):
 if not v: raise ValueError(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes(),object_pairs_hook=unique_object)
def function(text,entry):
 found=re.search(r'^define ptr @sub_'+format(entry,'x')+r'\([^\n]+\{\n(.*?)^}',text,re.M|re.S)
 need(found is not None,'Unique authentic trace entry');return found[1]
def blocks(body):
 result={};key='entry';result[key]=[]
 for line in body.splitlines():
  match=re.match(r'^(\w+):',line)
  if match:key=match[1];result[key]=[]
  else:result[key].append(line)
 return {k:'\n'.join(v) for k,v in result.items()}
def markers(body):
 return list(re.finditer(r'  (%\w+) = load i32, ptr %NEXT_PC, align 4\n  store i32 \1, ptr %PC, align 4',body))
def width(text):
 m=re.search(r'%\w+ = add i32 %\w+, (\d+)\n  store i32 %\w+, ptr %NEXT_PC',text)
 return int(m[1]) if m else 0
def recover(pre,guest,entry,rows):
 b=blocks(pre);todo=[('entry',entry)];assigned={};source={}
 while todo:
  label,pc=todo.pop()
  if label in assigned:need(assigned[label]==pc,'Source CFG join preserves exactPC');continue
  assigned[label]=pc;text=b[label];ms=markers(text);w=width(text)
  if ms and w:
   need(pc in rows and rows[pc]['width']==w,'Original instruction width matches actual pre-IR marker')
   source[label]=pc;row=rows[pc];op=row['mnemonic'];fall=pc+w
  else:row=None;op=None;fall=pc
  cond=re.search(r'br i1 %\w+, label %(\w+), label %(\w+)\s*$',text)
  branch=re.search(r'br label %(\w+)\s*$',text)
  if cond:
   need(row and op.startswith('j') and op!='jmp','Pre-trace conditional branch matches actual source')
   target=int(row['operands'],16);todo.extend(((cond[1],target),(cond[2],fall)))
  elif branch:
   target=int(row['operands'],16) if row and op=='jmp' and row['operands'].startswith('0x') else fall
   todo.append((branch[1],target))
  else:need('ret ptr' in text,'Reviewed pre-IR terminal')
 premarkers=markers(pre);gm=markers(guest)
 need(len(premarkers)==len(gm),'Optimized IR retains complete original instruction marker count')
 ordered=[]
 for key,text in b.items():
  for marker in markers(text):ordered.append((assigned[key],width(text[marker.start():]),key in source))
 need(len(ordered)==len(gm),'Every pre marker assigned original CFG')
 callbacks=[];mapping=[]
 for i,(pc,w,is_source) in enumerate(ordered):
  chunk=guest[gm[i].start():gm[i+1].start() if i+1<len(gm) else len(guest)]
  need(width(chunk)==w,'Optimized source marker width preserved')
  calls=list(re.finditer(r'(%\w+) = (?:tail )?call zeroext i8 @__remill_undefined_8\(\)',chunk))
  flags=[]
  for call in calls:
   tainted={call[1]};stores=[]
   for line in chunk[call.end():].splitlines():
    assign=re.match(r'  (%\w+) = (.+)',line)
    if assign and any(x in tainted for x in re.findall(r'%\w+',assign[2])):tainted.add(assign[1])
    store=re.match(r'  store i8 (%\w+), ptr (%\w+), align 1',line)
    if store and store[1] in tainted:stores.append(store[2])
   need(len(stores)==1,'Every undefined callback has one reviewed Statebyte destination '+hex(pc))
   pointer=stores[0];gep=re.search(re.escape(pointer)+r' = getelementptr inbounds(?: nuw)? i8, ptr %state, i32 (\d+)',chunk)
   need(gep is not None,'Callback exact State-offset identity');offset=int(gep[1]);need(offset in (2065,2067,2069,2071,2073,2077),'Arithmetic flag callback only');flags.append(offset)
  need(not flags or is_source,'No undefined callback in helper seam')
  if flags:callbacks.append(dict(pc=pc,mnemonic=rows[pc]['mnemonic'],callback_count=len(flags),State_offsets=flags))
  if is_source:mapping.append(dict(pc=pc,source_width=w,undefined_callback_count=len(flags)))
 total=len(re.findall(r'(?:tail )?call zeroext i8 @__remill_undefined_8\(\)',guest))
 need(total==sum(x['callback_count'] for x in callbacks),'Actual complete optimized undefined callback inventory')
 return callbacks,mapping
def main():
 out=ROOT/'reports/m4-crt-locale-batch-recovery/callbacks-r1';need(not out.exists(),'Fresh callback receipt')
 files={}
 def add(p,h=None):
  p=Path(p).absolute();v=sha(p);need(h is None or v==h,'Pinned callback dependency');files[normalized(str(p))]=v;return p
 interface=read(add(ROOT/'reports/m4-crt-locale-batch-recovery/interface-r1/instruction-contracts.json','194e2ca814869c500fd2948d9cc801d3ad7a8aef2367166379a5d0ad87e5a624'))
 rows={x['pc']:x for x in interface['instructions']};results={};entries={}
 for directory,h in [('reports/m4-crt-locale-batch/lifts-r1','ce3ab042ba40bd0b20119bb7b5fb0899c3849f9185e5fb1e91f123fb2e4c8025'),('reports/m4-crt-locale-batch-recovery/lifts-supplement-r1','94467367ace177e43df4cb4b237186a0a97320457fcea33fd85f55c633fd1956')]:
  path=ROOT/directory;report=read(add(path/'report.json',h));need(report['passed'],'Sealed literal preparation')
  for component,body in report['source_bodies'].items():
   pre=add(path/(component+'-pre.ll'));guest=add(path/(component+'-guest.ll'));host=add(path/(component+'-host.ll'),body['host_sha256'])
   callbacks,mapping=recover(function(pre.read_text(),body['entry']),function(guest.read_text(),body['entry']),body['entry'],rows)
   symbol='mw34_locale_batch_'+component+'_body';need('define ptr @'+symbol+'(' in host.read_text(),'Actual exported native symbol')
   results[component]=dict(entry=body['entry'],native_symbol=symbol,undefined_symbol='mw34_locale_batch_'+component+'_undefined_8' if callbacks else None,
    callback_sites=callbacks,actual_static_callback_calls=sum(x['callback_count'] for x in callbacks),mapped_original_instruction_blocks=len(mapping),source_marker_map=mapping)
   entries[str(body['entry'])]=symbol
 add(Path(__file__));out.mkdir(parents=True)
 def put(name,value):
  p=out/name;publish_bytes(p,(json.dumps(value,sort_keys=True,indent=2)+'\n').encode());add(p);return p
 p=put('callbacks.json',dict(schema='mw34-locale-batch-literal-generated-callbacks-v1',bodies=results,entry_to_native_symbol=entries))
 report=dict(schema='mw34-m4-locale-batch-callback-recovery-v1',passed=True,bodies=len(results),new_objects=2*len(results),callbacks_path=str(p),callbacks_sha256=sha(p),actual_static_callback_calls=sum(x['actual_static_callback_calls'] for x in results.values()),source_not_executed=True,native_not_executed=True,API_not_executed=True,files=files,physical_closure=verify_manifest(files))
 q=put('report.json',report);put('pins.json',dict(schema='mw34-m4-locale-batch-callback-pins-v1',files=files))
 print(json.dumps(dict(passed=True,report_sha256=sha(q),callbacks_sha256=sha(p))))
if __name__=='__main__':main()
