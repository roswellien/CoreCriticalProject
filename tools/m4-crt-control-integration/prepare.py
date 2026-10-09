"""Recover the complete game's control wrapper/thunk for fresh integration.

This prepares exact private static IR. It does not run game/provider code,
resolve the shared runtime's imports, or grant native execution admission.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import traceback

ROOT=Path(__file__).resolve().parents[2]
IMAGE_SHA='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
PROVIDER_SHA='2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
SEMANTICS_SHA='618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca'

def need(ok,why):
    if not ok: raise ValueError(why)

def digest(path):
    with Path(path).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

class PE:
    def __init__(self,path,expected,base):
        self.path=Path(path);need(digest(path)==expected,'Exact source image identity')
        self.data=self.path.read_bytes()
        e=self.dword(0x3C);need(self.data[:2]==b'MZ' and self.data[e:e+4]==b'PE\0\0','PE signature')
        need(self.word(e+4)==0x14C and self.word(e+24)==0x10B,'PE32 x86 source')
        self.base=self.dword(e+24+28);need(self.base==base,'Preferred source base')
        opt=self.word(e+20);self.sections=[]
        for i in range(self.word(e+6)):
            s=e+24+opt+40*i
            self.sections.append((self.dword(s+12),self.dword(s+16),self.dword(s+20),self.dword(s+36)))
        self.imports=self.dword(e+24+104);self.exports=self.dword(e+24+96)
    def word(self,o):return struct.unpack_from('<H',self.data,o)[0]
    def dword(self,o):return struct.unpack_from('<I',self.data,o)[0]
    def offset(self,va,n=1,rx=False):
        rva=va-self.base
        for address,extent,raw,flags in self.sections:
            if address<=rva and rva+n<=address+extent:
                need(not rx or (flags&0x60000000)==0x60000000 and not flags&0x80000000,'Source code RX permission')
                o=raw+rva-address;need(o+n<=len(self.data),'Source raw bounds');return o
        raise ValueError('Source address is not file-backed')
    def bytes(self,va,n,rx=False):
        o=self.offset(va,n,rx);return self.data[o:o+n]
    def rva32(self,rva):return self.dword(self.offset(self.base+rva,4))
    def string(self,rva):
        offset=self.offset(self.base+rva);end=self.data.index(0,offset,offset+256)
        return self.data[offset:end].decode('ascii')
    def import_slot(self,slot):
        for i in range(64):
            o=self.offset(self.base+self.imports+20*i,20)
            original,_,_,name,first=struct.unpack_from('<5I',self.data,o)
            if not (original or name or first):break
            for j in range(1024):
                value=self.rva32((original or first)+j*4)
                if not value:break
                if self.base+first+j*4==slot:
                    need(not value&0x80000000,'Named control provider import required')
                    return {'library':self.string(name),'name':self.string(value+2),'hint':self.word(self.offset(self.base+value,2)),'original_iat_value':self.rva32(first+j*4),'slot':slot}
        raise ValueError('Owning import slot absent')
    def export(self,name):
        o=self.offset(self.base+self.exports,40)
        _,_,_,_,_,ordinal,count,names,functions,nameptrs,ordinals=struct.unpack_from('<IIHHIIIIIII',self.data,o)
        for i in range(names):
            if self.string(self.rva32(nameptrs+4*i))==name:
                index=self.word(self.offset(self.base+ordinals+2*i,2));need(index<count,'Export index')
                rva=self.rva32(functions+4*index)
                return {'name':name,'ordinal':ordinal+index,'rva':rva,'address':self.base+rva}
        raise ValueError('Named provider export absent')

def main(output):
    need(output.is_relative_to(ROOT/'reports/m4-crt-control-integration') and not output.exists(),'Fresh owned private preparation')
    game=PE(ROOT/'MW3/Mech3.exe',IMAGE_SHA,0x400000)
    provider=PE(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',PROVIDER_SHA,0x78000000)
    owner=game.import_slot(0x5BB578);export=provider.export('_controlfp')
    need(owner['library'].lower()=='msvcrt.dll' and owner['name']=='_controlfp' and export['address']==0x780042E1,'Exact game/provider named linkage')
    call=game.bytes(0x5AC431,5,True)
    need(call[0]==0xE8 and 0x5AC436+struct.unpack_from('<i',call,1)[0]==0x5AC5A0,'Actual CRT-entry CALL target')
    wrapper=game.bytes(0x5AC5A0,19,True);thunk=game.bytes(0x5AC5D6,6,True)
    need(wrapper[:1]==b'\x68' and struct.unpack_from('<I',wrapper,1)[0]==0x30000 and wrapper[5]==0x68 and struct.unpack_from('<I',wrapper,6)[0]==0x10000,'Exact control new/mask arguments')
    need(wrapper[10]==0xE8 and 0x5AC5AF+struct.unpack_from('<i',wrapper,11)[0]==0x5AC5D6 and wrapper[15:]==bytes.fromhex('83c408c3'),'Complete wrapper call/caller cleanup/RET')
    need(thunk[:2]==bytes.fromhex('ff25') and struct.unpack_from('<I',thunk,2)[0]==0x5BB578,'Complete owning import tail JMP')
    sem=ROOT/'local/tools/remill-x87-control-repair/semantics/x86.bc';need(digest(sem)==SEMANTICS_SHA,'Exact repaired semantics')
    lift=ROOT/'local/tools/remill-x87-control-repair/remill-lift-control-21.exe'
    llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
    output.mkdir(parents=True)
    (output/'prepare-source.py').write_bytes(Path(__file__).read_bytes())
    commands=[]
    try:
        dense=bytearray([0xCC]*(0x5AC5DC-0x5AC5A0));dense[:19]=wrapper;dense[0x36:0x3C]=thunk
        (output/'lift-input.bin').write_bytes(dense)
        (output/'crt-entry-call.bin').write_bytes(call)
        source_ranges=[]
        for entry,body in ((0x5AC5A0,wrapper),(0x5AC5D6,thunk)):
            path=output/f'source-{entry:x}.bin';path.write_bytes(body)
            source_ranges.append({'address':entry,'size_bytes':len(body),'file_offset':game.offset(entry,len(body),True),'sha256':digest(path),'complete_function':True})
            flags=['--arch=x86','--os=windows','--address='+str(0x5AC5A0),'--entry_address='+str(entry),'--bytes='+dense.hex(),'--semantics_dir='+str(sem.parent),'--ir_out='+str(output/f'guest-{entry:x}.ll')]
            (output/f'flags-{entry:x}.txt').write_text('\n'.join(flags)+'\n')
            result=subprocess.run([str(lift),*flags],capture_output=True)
            log=output/f'lift-{entry:x}.log';log.write_bytes(result.stdout+result.stderr)
            commands.append({'program':str(lift),'flags_file':str(output/f'flags-{entry:x}.txt'),'exit_code':result.returncode,'log_path':str(log)})
            need(result.returncode==0,'Complete static game function lift')
        command=[str(llvm/'llvm-link.exe'),str(output/'guest-5ac5a0.ll'),str(output/'guest-5ac5d6.ll'),'-S','-o',str(output/'guest.ll')]
        result=subprocess.run(command,capture_output=True);(output/'link.log').write_bytes(result.stdout+result.stderr)
        commands.append({'arguments':command,'exit_code':result.returncode,'log_path':str(output/'link.log')});need(result.returncode==0,'Complete two-body graph link')
        guest=(output/'guest.ll').read_text()
        need(set(re.findall(r'^define ptr @([^ (]+)',guest,re.M))=={'sub_5ac5a0','sub_5ac5d6'} and '__remill_missing_block' not in guest,'Complete definitions with no missing-block fallback')
        need(guest.count('@__remill_jump(')==2,'One actual imported tail-JMP call plus declaration')
        report={'passed':True,'scope':'Exact complete game control wrapper/thunk static preparation only; typed import-tail bridge, actual connected comparison and native compilation pending','game_image_sha256':IMAGE_SHA,'provider_sha256':PROVIDER_SHA,'import_owner':owner,'provider_export':export,'complete_source_ranges':source_ranges,'crt_entry_call':{'pc':0x5AC431,'target':0x5AC5A0,'return_pc':0x5AC436,'complete_CRT_entry_executed':False,'sha256':digest(output/'crt-entry-call.bin')},'provider_CALL':{'pc':0x5AC5AA,'target':0x5AC5D6,'return_pc':0x5AC5AF,'abi':'cdecl','argument_bytes':8,'mask':0x30000,'new':0x10000,'tail_JMP_slot':0x5BB578},'typed_bridge_requirements':['Retain the already-pushed provider return word across the import tail JMP; no second guest CALL frame.','Preserve original raw IAT dword in native image; named-slot dispatch has explicit provider admission, not a host-pointer fixup.','Return actual compiled provider State to wrapper continuation5AC5AF, then execute its real ADD ESP,8/RET.','Keep shared Runtime r9 frozen; any new frame-transfer/service API requires separate compiled controls and review.','Carry updated State and FX CW into subsequent numerical callbacks with actual per-callback host isolation.'],'commands':commands,'shared_Runtime_r9_changed':False,'native_body_executed':False,'whole_M4_complete':False}
        (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        inputs=[Path(__file__),game.path,provider.path,sem,lift,llvm/'llvm-link.exe',ROOT/'reports/m4-crt-control/independent-review-r4/report.json',ROOT/'reports/m4-crt-control/independent-review-r4/pins.json']
        files={str(p):digest(p) for p in inputs}
        files.update({str(p):digest(p) for p in output.iterdir() if p.is_file()})
        (output/'pins.json').write_text(json.dumps({'files':files},indent=2)+'\n')
        print(json.dumps({'passed':True,'complete_game_functions':2,'owning_IAT':hex(owner['slot']),'provider_return':hex(0x5AC5AF),'native_admission':False,'report_sha256':digest(output/'report.json')}))
    except Exception:
        (output/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path)
    main(parser.parse_args().output.resolve())
