"""Read-only native scheduler/host continuity within the already-open reader."""
import collections,struct
def need(v,s):
 if not v:raise ValueError(s)
def cpu(b):return struct.unpack('<10I',b)
def host(fx,after,env,env_after):
 need(fx[:5]==after[:5]and fx[24:28]==after[24:28]and env==env_after,'Outside-return numerical and entire ENV preservation')
 need(all(fx[32+16*i:42+16*i]==after[32+16*i:42+16*i]for i in range(8)),'Outside-return all raw80 slots')
def audit(reader,m,old):
 counts=collections.Counter();entries=reader.words('selected-table.bin',130);registration=set(reader.words('registration-roots.bin',101));raw=reader.data('extra-pages.bin');need(len(raw)%4==0,'Whole extra-page DWORDs');pages=struct.unpack('<'+'I'*(len(raw)//4),raw);need(len(set(pages))==len(pages)==29 and set((0x7810a000,0x78145000,0x78146000))<=set(pages),'All29 distinct external provider/game pages');growth=[]
 for seq in range(6):
  prefix=f'sequence-{seq}/';summary=reader.data(prefix+'summary.bin');host(summary[48:560],summary[560:1072],summary[1072:1100],summary[1100:1128]);counts['selected_host_returns']+=1
  before=bytearray(reader.data(prefix+'caller-projection-before/State.bin'));after=reader.data(prefix+'caller-projection-after/State.bin');m.statecpu(before,cpu(reader.data(prefix+'caller-projection-after/CPU.bin')));need(before==after,'One external CPU-only caller projection');need(reader.data(prefix+'caller-projection-before/FX.bin')==reader.data(prefix+'caller-projection-after/FX.bin'),'Caller projection preserves whole guest FX');counts['external_cpu_projections']+=1;previous=None
  for phase,entry in enumerate(entries):
   record=reader.data(prefix+f'phase-{phase}.bin');sb=record[141540:145044];sa=record[145044:148548];actual=cpu(record[36:76]);previous_state=bytearray(previous[145044:148548]if previous else after);source_cpu=list(cpu(previous[76:116]if previous else reader.data(prefix+'caller-projection-after/CPU.bin')));source_cpu[4]-=4;source_cpu[9]=entry;need(actual==tuple(source_cpu),'Exact40B CPU scheduler source CALL continuity');m.statecpu(previous_state,source_cpu);previous_state=previous_state if entry in registration or entry==0x4c19f0 else m.beforestate(previous_state,source_cpu,entry);need(sb==previous_state,'Complete3504B actual scheduler State continuity');old.projection(m,record,sb);old.projection(m,record,sa,True);counts['complete_State_and_projection_checks']+=2
   if previous:
    need(previous[71908:141540]==record[2276:71908],'Entire17 fixed pages persist between roots');need(previous[628:1140]==record[116:628]and previous[2192:2220]==record[2164:2192],'Entire512B FX and28B ENV continuity');counts['whole_fixed_page_carries']+=17
    for page in pages:need(reader.data(prefix+f'phase-{phase-1}-after-page-{page}.bin')==reader.data(prefix+f'phase-{phase}-before-page-{page}.bin'),'Entire4096B external page persists');counts['whole_extra_page_carries']+=1
    need(reader.data(prefix+f'phase-{phase-1}-after-registry.bin')==reader.data(prefix+f'phase-{phase}-before-registry.bin'),'Actual registry owner summary persists');counts['registry_carries']+=1
   previous=record
  need(summary[4632:8136]==previous[145044:148548]and summary[77768:147400]==previous[71908:141540],'Selected summary is actual final State/pages');counts['whole_selected_summaries']+=1
  host(reader.data(prefix+'growth-cleanup-host-before-FX.bin'),reader.data(prefix+'growth-cleanup-host-after-FX.bin'),reader.data(prefix+'growth-cleanup-host-before-ENV.bin'),reader.data(prefix+'growth-cleanup-host-after-ENV.bin'));counts['growth_cleanup_host_returns']+=1;growth.append(reader.words(prefix+'growth-replay-count.bin',1)[0])
 return dict(counts=dict(counts),growth_replays=growth,scope='Actual scheduler/host continuity only; independent literal source semantic gate remains separate')
