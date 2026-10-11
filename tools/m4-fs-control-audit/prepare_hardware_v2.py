from pathlib import Path
H=Path(__file__).resolve().parent
def main():
 p=H/'diagnose_hardware.py';t=p.read_text();t=t.replace(" for row in value['levels']:"," for row in [dict(row,attempt=attempt) for row in value['levels'] for attempt in ('first','retry')]:")
 t=t.replace("sample=owner.read_bytes('case-0/first.bin')","sample=owner.read_bytes('case-0/'+row['attempt']+'.bin')")
 t=t.replace("owner.read_bytes('case-0/first-cleanup-hardware-before.bin')","owner.read_bytes('case-0/'+row['attempt']+'-cleanup-hardware-before.bin')").replace("owner.read_bytes('case-0/first-cleanup-hardware-after.bin')","owner.read_bytes('case-0/'+row['attempt']+'-cleanup-hardware-after.bin')").replace("owner.read_bytes('case-0/first-causal-guest-ENV.bin')","owner.read_bytes('case-0/'+row['attempt']+'-causal-guest-ENV.bin')")
 t=t.replace("out/(row['level']+'-'+name)","out/(row['level']+'-'+row['attempt']+'-'+name)").replace("levels[row['level']]={","levels[row['level']+'-'+row['attempt']]={'attempt':row['attempt'],")
 t=t.replace("'scope':'Independent actual failure diagnosis only; complete outside-return hardware assertions remain required'","'scope':'Complete failed case0 diagnosis: ordinary six-root return is exact, but naked same-finished-Session replay plus caller C++ catch loses actual legacy ENV metadata. This is a fixture/wrapper refusal-boundary issue; no production or initializer acceptance. Later authored outer wrapper may preserve whole attempt explicitly; no retroactive callee-only exception claim.'")
 out=H/'diagnose_hardware_v2.py';assert not out.exists();out.write_text(t,encoding='utf-8',newline='\n')
if __name__=='__main__':main()
