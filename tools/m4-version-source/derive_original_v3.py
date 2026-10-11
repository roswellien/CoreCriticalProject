"""Add measured original API hardware ABI/projection guards before admission."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
p=P/'original_observer_v2.hpp';s=p.read_text()
a='if(side==1){version_API_hardware[API]=version_hardware;'
b='''if(side==1){const auto&hb=version_hardware.before;const auto&ha=version_hardware.after;require(hb.cpu.pc==version_targets[API]&&ha.cpu.esp==hb.cpu.esp+4*(version_argc[API]+1)&&ha.cpu.ebx==hb.cpu.ebx&&ha.cpu.ebp==hb.cpu.ebp&&ha.cpu.esi==hb.cpu.esi&&ha.cpu.edi==hb.cpu.edi,"Actual original VERSION stdcall hardware argument consumption and nonvolatile registers");require(version_cpu.eax==ha.cpu.eax&&version_cpu.ecx==ha.cpu.ecx&&version_cpu.edx==ha.cpu.edx&&version_cpu.ebx==ha.cpu.ebx&&version_cpu.ebp==ha.cpu.ebp&&version_cpu.esi==ha.cpu.esi&&version_cpu.edi==ha.cpu.edi&&version_cpu.flags==ha.cpu.flags&&!std::memcmp(version_fx,ha.fx,512)&&!std::memcmp(version_env,ha.env,28),"Whole actual original VERSION hardware GPR flags FX ENV projection with explicit source ESP PC relocation");require(error==version_API_after_error,"Actual original VERSION immediate LastError retained before post observation");version_API_hardware[API]=version_hardware;'''
s=once(s,a,b);q=P/'original_observer_v3.hpp';assert not q.exists();q.write_text(s)
p=P/'prepare_original_v2.py';s=p.read_text();s=once(s,"T/'original_observer_v2.hpp'","T/'original_observer_v3.hpp'")
s=once(s,"  pin(T/'derive_original_v2.py')","  pin(T/'derive_original_v3.py');pin(T/'original_observer_v2.hpp','"+sha(P/'original_observer_v2.hpp')+"');pin(R/'reports/m4-version-source/original-preparation-r2/report.json','24467c5bcbfaf6cd67ef1a74c99a7d53aa2c8c5f7d6a44dae2b3a04fb5b648d5');pin(R/'reports/m4-version-source/original-build-r2/build.json','bded33860f55aad349e9b7ace40a9d267fa664a26a15d8da4f747d8c77982b48');pin(T/'derive_original_v2.py')")
s=once(s,"[T/'prepare_original_v2.py',T/'prepare_original_v1.py'","[T/'prepare_original_v3.py',T/'prepare_original_v2.py',T/'prepare_original_v1.py'")
s=once(s,'conditional_branch_relocation=True,actual_typed_version_provider=True','conditional_branch_relocation=True,actual_API_hardware_stdcall_consumption_guard=True,whole_actual_GPR_flags_FX_ENV_projection_guard=True,immediate_post_API_LastError_guard=True,actual_typed_version_provider=True')
q=P/'prepare_original_v3.py';assert not q.exists();q.write_text(s);print(json.dumps(dict(recipe=str(q),sha256=sha(q),original_executed=False)))
