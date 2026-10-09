        progress=struct.unpack('<8I',reader.read_bytes(case+'/heap-return-progress.bin'));public=list(struct.unpack('<6I',reader.read_bytes(case+'/heap-return-public.bin')))
        wanted=(int(mode in UNWOUND),int(mode in UNWOUND),int(mode in MODEPUB),int(mode in MODEPUB),int(mode in RETBEFORE),int(mode in INITRET))
        need(progress==(1,*wanted,0),'Exact canonical private source-store/RET progression and no live opaque token after actual cleanup')
        if mode==93:public[3]^=1
        if mode==94:public[2]=1
        if mode==158:public[2]=0
        need(tuple(public)==wanted,'Only explicitly refused public publication/value forgery differs from immutable private progression')
        if mode in MODEPUB:need(tuple(events[44:48])==(12,0x780039eb,0x78035004,1) and ledger[31]==(0x780039eb,0x78035004,1,4,1),'Authentic mode MOV and event are committed together from actual selector result1')
        if mode in INITRET:need(tuple(events[48:52])==(13,0x78003a0b,0x78001843,0x20001858) and ledger[34]==(0x78003a0b,0x20001858,0x78001843,4,0),'Initializer RET commits genuine original caller frame and event')
        need(hashlib.sha256(reader.read_bytes(case+'/heap-create-before/heap-provider.bin')).hexdigest()=='72922b45de858dc84ab5a08a8626acf0fca8487bd1e1cba955a3c0afba30e6ba','Immutable whole77-byte provider source includes caller continuation and success RET')
        if mode==0:
            expected_state=bytearray(reader.read_bytes(case+'/heap-version-selector-return-after/state.bin'));need(len(expected_state)==3504,'Complete actual selector-return State extent')
            for offset,value in ((2065,1),(2067,1),(2069,1),(2071,0),(2073,1),(2077,0)):expected_state[offset]=value
            struct.pack_into('<I',expected_state,2312,0x2000185c);struct.pack_into('<I',expected_state,2472,0x78001843)
            need(reader.read_bytes(case+'/independent-after/state.bin')==expected_state,'Complete3504-byte source State follows exact CMP1,2/initializer PUSH/POP/RET effects')
            need(ledger[31:35]==[(0x780039eb,0x78035004,1,4,1),(0x78003a08,0x20001854,1,4,1),(0x78003a0a,0x20001854,1,4,0),(0x78003a0b,0x20001858,0x78001843,4,0)],'Four exact added genuine source accesses')
            for page in PAGES:
                before=bytearray(reader.read_bytes(case+'/heap-version-selector-return-after/page-'+str(page)+'.bin'))
                if page==0x78035000:struct.pack_into('<I',before,4,1)
                if page==0x20001000:struct.pack_into('<I',before,0x854,1)
                need(reader.read_bytes(case+'/independent-after/page-'+str(page)+'.bin')==before,'All21 complete pages after selector RET change only via literal mode MOV and PUSH1')
        for domain,phase,phase_progress,pc,sp in ((UNWOUND,'heap-return-mode-store-before',(1,1,1,0,0,0,0,1),0x780039eb,0x20001858),(MODEPUB,'heap-return-mode-store-after',(1,1,1,1,1,0,0,1),0x780039eb,0x20001858),(RETBEFORE,'heap-return-initializer-return-before',(1,1,1,1,1,1,0,1),0x78003a0b,0x20001858),(INITRET,'heap-return-initializer-return-after',(1,1,1,1,1,1,1,1),0x78001843,0x2000185c)):
            if mode in domain:
                phases.add(phase);need(struct.unpack('<8I',reader.read_bytes(case+'/'+phase+'/heap-return-progress.bin'))==phase_progress,'Private exact original source phase progress and live original HANDLE token')
                phase_cpu=struct.unpack('<10I',reader.read_bytes(case+'/'+phase+'/state-cpu.bin'));need(phase_cpu[4]==sp and phase_cpu[9]==pc,'Authentic source checkpoint State PC/SP chronology')
                phase_registry=struct.unpack('<18Q',reader.read_bytes(case+'/'+phase+'/heap-create-registry.bin'));need(phase_registry[4]==own[0] and phase_registry[7]==1 and phase_registry[9]==phase_registry[10]==0,'Original full64HANDLE still live before genuine source exit and actual cleanup')
