"""All fourth-root formatter histories and native lifetime rows join independent source."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('compare_native_witnesses_v4.py');s=p.read_text()
def one(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
s=s.replace("native-source-r9/report.json","native-family-source-r3/report.json").replace('0f2e817ff2bf938e32be26d7018d3921be5142461bf54ddfe70e0a676daa2306','52d776251f86a787db71d4b15a91f174737099986585c8dfe7a0d5c9c452e521')
one("len(sources)==6,'All six literal source phases'","len(sources)==8,'All eight literal source phases'")
one("fixture-execution-r4/report.json','55ecbdc1a115f73ab046ea92f6e33f5af0020d92a530dbe2a3e145af7d37bba0'","family-fixture-execution-r1/report.json','5ecd8260c6625a589c8e1c517b41c1c7f8deddfbbeb1b61825f6e337c1767297'")
one("D=load('formatting_witness_direct'",'''family=read(ROOT/'reports/m4-formatting-native/preparation-r18/family-contracts.json')
  normal['cases'].append(dict(root_contract=dict(owned_pointer_field=0x60b66c),owned_accesses=family['additional_format_owned_order']))
  D=load('formatting_witness_direct' ''')
one('for phase in range(3):','for phase in range(4):')
one("actual-after-root-2/formatting-status.bin","actual-after-root-3/formatting-status.bin")
one("len(live)==len(cleaned)==4,'Producer plus three actual formatter owners'","len(live)==len(cleaned)==8,'Producer plus four formatter and three actual MFC owners'")
one("((1,0)if before[1]==0x31000000 else(0,1))","((1,0)if before[1]==0x31000000 or before[6]==4 else(0,1))")
one("site_names={r['pc']:r['API']for r in static['API_sites']};enters=","site_names={r['pc']:r['API']for r in static['API_sites']};site_names.update({0x7810a30b:'EnterCriticalSection',0x7810a35e:'LeaveCriticalSection'});enters=")
one("summary[9:16]==(4,1,3,5,5,0,0)","summary[9:16]==(8,4,4,5,5,0,0)")
one('pin(__file__);(out/',"pin(__file__);pin(ROOT/'tools/m4-formatting-source/compare_native_witnesses_v4.py');(out/")
one("proofs.append(dict(level=level,phase=phase",'''if r['root']==0x4e1ca0:
     owners=r['mixed_owners'];records=rows(a,stem+'mfc-call-records.bin',32)if stem+'mfc-call-records.bin'in a.entries else rows(a,stem+'mfc-call-frames.bin',32)
     actual_fs=rows(a,stem+'fs-owned-accesses.bin',16);expected_fs=[]
     for i,row in enumerate(source_accesses):
      pc,address,value,width,writing=row
      if i<base:continue
      for owner in owners:
       if owner['guest']<=address and address+width<=owner['guest']+owner['extent']:
        matches=[record for record in records if record[2]==r['root']and record[4]==owner['allocation_CALL_pc']and record[16]==owner['guest']and record[18]==owner['generation']];need(len(matches)==1,'One exact mixed MFC private invocation/generation')
        record=matches[0];need(record[7]==owner['requested']and record[17]==owner['native']and record[19]==owner['extent']and record[21]==record[23]==1,'Whole allocation/publication completion joins actual owner')
        expected_fs.append((1,len(expected_fs),r['root'],pc,address,width,value,writing,r['root'],owner['allocation_CALL_pc'],owner['guest'],owner['generation'],owner['native'],address-owner['guest'],record[1],i+1))
     equal(actual_fs,expected_fs,'Every complete mixed private FS owner record derives from literal owned operand and actual MFC occurrence');need(len(expected_fs)==10,'Ten complete mixed owner rows');counts['literal_private_mixed_owner_rows']+=10
    proofs.append(dict(level=level,phase=phase''')
exec(compile(s,str(p),'exec'),globals())
