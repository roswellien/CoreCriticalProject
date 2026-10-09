"""Independent physical table, normal FS-frame and additive lift review."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/analysis'))
from pe import PEImage

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main(name):
 out=ROOT/'reports/m4-fs-review'/name;assert not out.exists();out.mkdir(parents=True)
 pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 parent=pin(ROOT/'reports/m4-joint-startup103-root/acceptance-r1/report.json','13cc2567f30f2dae2d12991a3a76aa6c953c70a49148dc4ed13df34837b14c7c')
 assert json.loads(parent.read_bytes())['passed']
 recovery=pin(ROOT/'reports/m4-fs-source/recovery-r3/report.json','17c7840c58bcdce2a82989d141f202cbb25540b6c29b4f314c06c0d1c2bf3a6b')
 r=json.loads(recovery.read_bytes());assert r['passed']
 for p,h in r['files'].items():pin(p,h)
 c=json.loads(pin(recovery.parent/'instruction-contracts.json').read_bytes())
 game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');pe=PEImage(game.read_bytes())
 def raw(pc,n):
  off,_=pe.rva_range(pc-pe.image_base,n);return pe.data[off:off+n]
 rows={x['pc']:x for x in c['instructions']};assert len(rows)==len(c['instructions'])==307
 checked=0
 for x in rows.values():assert raw(x['pc'],x['width']).hex()==x['bytes_hex'];checked+=x['width']
 selected=c['selected_order'];assert len(selected)==109
 actual=[]
 for slot in range(145):
  value=int.from_bytes(raw(0x5e0000+4*slot,4),'little')
  if value:actual.append((0x5e0000+4*slot,value))
 assert len(actual)==144
 for x in selected:assert (x['slot'],x['entry'])in actual
 assert [x['slot']for x in selected]==sorted(set(x['slot']for x in selected))
 prior=json.loads(pin(ROOT/'reports/m4-joint-startup103/preparation-r1/report.json','b8d18bc4765dee58c6a4e62082f2d74497833be1c8df0eee76532807c841bde6').read_bytes())
 new=set(x['entry']for x in selected)-set(x['entry']for x in prior['selected_order'])
 assert new=={0x46ab30,0x48f250,0x4b4c10,0x4c3250,0x4cfe80,0x4d4830}
 assert set(x['entry']for x in c['roots'])==new
 frames=c['FS_frame_contracts'];assert {f['entry']for f in frames}=={0x4e78d0,0x48f290,0x4d48f0}
 reviewed=[]
 for f in frames:
  assert f['installed_record_entry_ESP_offset']==f['epilogue_read_entry_ESP_offset']==-12
  assert f['normal_return_entry_ESP_offset']==0 and not f['handler_executed']
  expected=[{'offset':0,'value':'Actual BEFORE FS:[0]'},{'offset':4,'value':f['handler']},{'offset':8,'value':0xffffffff}]
  assert f['record_fields']==expected
  offsets={int(k):v for k,v in f['static_ESP_offsets'].items()}
  assert offsets[f['read']]==-8 and offsets[f['install']]==-12 and offsets[f['final_ret']]==0
  assert offsets[f['saved_load']]+f['saved_offset']==-12
  assert raw(f['entry'],2)==b'\x6a\xff' and raw(f['entry']+2,5)==b'\x68'+f['handler'].to_bytes(4,'little')
  assert raw(f['read'],6)==bytes.fromhex('64a100000000')
  assert raw(f['install'],7)==bytes.fromhex('64892500000000')
  assert raw(f['restore'],7)==bytes.fromhex('64890d00000000')
  assert raw(f['final_ret'],1)==b'\xc3'
  for x in f['literal_source_rows']:assert raw(x['pc'],x['size']).hex()==x['bytes']
  reviewed.append({k:f[k]for k in('entry','handler','read','install','saved_load','saved_offset','restore','final_ret')})
 fs_sites=[x for x in rows.values()if 'fs:'in x['operands'].lower()];assert len(fs_sites)==9
 assert 0 not in c['source_data_pages'] and c['FS_base_is_runtime_or_actual_windows_TIB'] and c['FS_offset_zero_is_not_game_page_zero'] and not c['AFTER_machine_seed']
 gh=json.loads(pin(ROOT/'reports/m4-fs-ghidra/export-r1/report.json').read_bytes());assert gh['passed']and gh['functions']==21 and not gh['missing']and gh['cold_imports']==0
 for p,h in gh['files'].items():pin(p,h)
 lifts=json.loads(pin(ROOT/'reports/m4-fs-source/lifts-r1/report.json','f5af3ee18fd942c5f58226b0ae98fca29d7bdc93877d7cfdd624a43cc0aa1ab8').read_bytes());assert lifts['passed']and len(lifts['source_bodies'])==17
 for p,h in lifts['files'].items():pin(p,h)
 pin(__file__);pin(ROOT/'tools/analysis/pe.py')
 value=dict(passed=True,scope='Physical source/table/lift and normal frame contract review only; actual chain observations and semantic execution remain required',selected_roots=109,new_roots=6,normal_frames=reviewed,FS_sites=9,unique_physical_rows=307,physical_row_bytes=checked,new_literal_bodies=17,warm_Ghidra_functions=21,initializer_credit=False,native_executed=False,original_executed=False,handler_execution=False,files=pins)
 (out/'report.json').write_text(json.dumps(value,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n')
 print(json.dumps({k:value[k]for k in('passed','selected_roots','new_roots','FS_sites','unique_physical_rows','physical_row_bytes','new_literal_bodies')}))
if __name__=='__main__':main(sys.argv[1])
