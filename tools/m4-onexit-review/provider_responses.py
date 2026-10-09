"""Actual scalar/owned-byte API witnesses for the independent provider model.

Only finite actual API results and allocation-byte witnesses enter this model.
No captured AFTER registers, flags, stack, globals or pages are accepted inputs.
"""
from pathlib import Path
import struct, sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-crt-locale-batch-model-review'))
import interpreter_v2 as I
import batch as B

NEW_CONTRACTS={
    0x780015B5:dict(name='HeapSize',slot=0x7802E1DC,raw=0x34BD0,argc=3,tail=False,void=False),
    0x78011C27:dict(name='HeapReAlloc',slot=0x7802E0B4,raw=0x3464A,argc=4,tail=False,void=False),
}

class ActualResponses(B.ActualResponses):
    def __init__(self,facts):
        super().__init__(facts);self.contracts.update(NEW_CONTRACTS);self.growth=[]

    def __call__(self,m,target):
        site=m.PCs[-1]
        if site not in NEW_CONTRACTS:
            before=self.index
            super().__call__(m,target)
            if before<self.index and self.facts[before]['name']=='HeapAlloc':
                allocation=self.allocations[-1]
                allocation.update(requested=allocation['extent'],capacity=0,previous_native=0)
            return
        I.need(self.index<len(self.facts),'Complete finite actual changed API witness')
        fact=self.facts[self.index];w=fact['words'];c=self.contracts[site]
        I.need(len(w)==32 and tuple(w[:2])==(1,self.index),'Indexed actual changed API32Q record')
        frame=m.reg('esp');ret=int.from_bytes(m.bytes(frame,4),'little')
        args=tuple(int.from_bytes(m.bytes(frame+4+4*n,4),'little') for n in range(c['argc']))
        I.need(target==c['raw'] and tuple(w[2:8])==(site,c['slot'],c['raw'],frame,ret,c['argc']),
               'Independent source-derived API IAT/frame/arity')
        I.need(tuple(w[20:20+c['argc']])==args and not w[19] and w[14]==w[15]==1,
               'Exact actual source arguments and completed genuine stdcall')
        I.need(w[9]==w[11] and w[9]<=0xFFFFFFFF and w[10]<=0xFFFFFFFF,'Actual caller LastError restored')
        I.need(args[0]==0x48450001 and args[1]==0,'Source same-owned-heap token and original flags0')
        allocation=next((a for a in self.allocations if a['live'] and a['guest']==args[2]),None)
        I.need(allocation and allocation['native']==w[16] and w[16]%16==0,
               'Exact full-width privately owned current native allocation')
        oldextent=allocation['extent'];oldbytes=m.bytes(allocation['guest'],oldextent)
        I.need(fact['inputs']==[oldbytes],'Full independent pre-API owned source bytes')
        self.active=self.index;tag='locale-api-'+str(self.index)
        m.snapshot(tag+'-before');m.emit('api-before',index=self.index,fact=fact,contract=c)
        if c['name']=='HeapSize':
            result=w[8]
            I.need(result==w[17],'Measured native SIZE_T capacity retained literally')
            if result==(1<<64)-1:
                I.need(w[12]==0xFFFFFFFF and not fact['outputs'],'Actual SIZE_T(-1) mapped to original DWORD failure')
                m.snapshot(tag+'-after');returned=0xFFFFFFFF
            else:
                I.need(oldextent<=result<=allocation['mapped'] and result<=1048576 and w[12]==result,
                       'Actual measured capacity fits currently owned finite backing')
                I.need(len(fact['outputs'])==1 and len(fact['outputs'][0])==result
                       and fact['outputs'][0][:oldextent]==oldbytes,'Full actual capacity-byte witness preserves previous owned bytes')
                raw=fact['outputs'][0]
                # This is an allocation alias observation/copy, not a HeapSize
                # output buffer or an architectural instruction.
                for offset in range(0,len(raw),4):
                    width=min(4,len(raw)-offset)
                    m.write(allocation['guest']+offset,int.from_bytes(raw[offset:offset+width],'little'),width,
                            domain='transport',pc=site)
                allocation['extent']=allocation['capacity']=result
                I.need(w[13]==result,'Exact committed measured-capacity byte count')
                m.snapshot(tag+'-after');returned=result
        else:
            capacity=allocation.get('capacity',0)
            I.need(capacity==w[17] and capacity==oldextent and capacity>0,
                   'Reallocation input capacity came from prior actual source msize')
            source_frames=[f for f in m.call_stack if f[0]==0x780019F1]
            I.need(source_frames,'Genuine original realloc caller frame')
            requested=int.from_bytes(m.bytes(source_frames[-1][1]+8,4),'little')
            rounded=(requested+15)&~15
            I.need(requested==capacity+16 and args[3]==rounded and rounded>capacity and rounded<=1048576,
                   'Original msize+16 source request and mode1 rounding')
            g=tuple(fact['growth']);I.need(len(g)==32 and g[:3]==(1,self.index,site),'Exact API-associated actual growth32Q')
            I.need(g[3:11]==(allocation['guest'],allocation['native'],allocation['generation'],
                             allocation.get('requested',oldextent),oldextent,capacity,requested,rounded),
                   'Independent old allocation/generation/extent/capacity/request identity')
            result=w[8];I.need(g[11]==result and g[12]==w[10],'Actual full pointer and raw LastError witness')
            if not result:
                I.need(w[12]==0 and fact['outputs']==[oldbytes]
                       and g[13:18]==(allocation['guest'],allocation['native'],allocation['generation'],oldextent,capacity)
                       and not any(g[18:22]) and g[23]==1,
                       'Actual NULL keeps old pointer, alias, generation and all old bytes')
                m.snapshot(tag+'-after');returned=0
            else:
                I.need(result%16==0 and len(fact['outputs'])==1 and len(fact['outputs'][0])==rounded
                       and fact['outputs'][0][:oldextent]==oldbytes,'Actual aligned reallocation and preserved old bytes')
                raw=fact['outputs'][0];moved=result!=allocation['native'];guest=self.allocation_cursor if moved else allocation['guest']
                oldguest=allocation['guest'];allocation['previous_native']=allocation['native'];allocation['native']=result
                I.need(g[13]==guest and g[14]==result and g[16:20]==(rounded,0,int(moved),1)
                       and g[20]==rounded and g[21:24]==(0,1,0) and not any(g[24:]),
                       'Measured moved/native/alias/complete-copy outcome')
                m.snapshot(tag+'-after')
                if moved:
                    mapped=(rounded+4095)&~4095
                    I.need(not any(p<=guest<p+len(b) or guest<=p<guest+mapped for p,b in m.memory.items()),
                           'Fresh disjoint research alias for actual native move')
                    m.memory[guest]=bytearray(mapped);self.allocation_cursor+=mapped
                    allocation['mapped']=mapped
                self.generation+=1
                I.need(g[15]==self.generation,'Fresh monotonically carried owner generation')
                allocation.update(guest=guest,requested=requested,extent=rounded,capacity=0,generation=self.generation,initial=raw)
                for offset in range(0,rounded,4):
                    width=min(4,rounded-offset)
                    m.write(guest+offset,int.from_bytes(raw[offset:offset+width],'little'),width,domain='transport',pc=site)
                if moved:m.memory.pop(oldguest)
                I.need(w[12]==guest and w[13]==rounded,'Actual finite returned alias and committed byte count')
                self.growth.append(g);returned=guest
        m.api_return(site,c['argc'],returned)
        m.snapshot(tag+'-returned');self.index+=1;self.active=None

    def completed_registry(self,m,expected):
        begin=int.from_bytes(m.bytes(0x7803788C,4),'little');next_=int.from_bytes(m.bytes(0x78037888,4),'little')
        owned=next((a for a in self.allocations if a['guest']==begin and a['live']),None)
        I.need(owned is not None and (next_-begin)==4*len(expected) and (next_-begin)<=owned['extent'],
               'Literal registry globals reference the same current live owner and exact entry count')
        raw=m.bytes(begin,next_-begin);actual=struct.unpack('<'+str(len(expected))+'I',raw)
        I.need(actual==tuple(expected),'Actual source ordered callback addresses')
        return dict(begin=begin,next=next_,callbacks=actual,native=owned['native'],capacity=owned.get('capacity',0),
                    callback_execution=False,AFTER_machine_seed=False)
