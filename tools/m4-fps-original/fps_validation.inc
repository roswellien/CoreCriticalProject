   # Independent actual cdecl observer geometry. This validates observations,
   # not a literal CRT/native formatter implementation.
   fcount=words(capture.data(stem+'fps-count.bin'))[0];fblob=capture.data(stem+'fps-snapshots.bin');segments=capture.data(stem+'fps-segments.bin');need(fcount<=8 and not(fcount%2)and len(fblob)==fcount*529700 and len(segments)==fcount*40,'Complete bounded FPS sides and raw selector records')
   if root['root']!=0x40f000:need(fcount==0,'FPS service not reached by earlier null-format roots')
   fps_pair=[]
   for i in range(fcount):
    snap=fblob[i*529700:(i+1)*529700];h=words(snap,0,16);cpu=words(snap,64,10);fx=snap[104:616];env=snap[616:644];frame=snap[644:708];view=snap[708:724];side=i%2
    need(h[:5]==(1,i,root['root'],side,cpu[9])and h[7]==fps_identity[1]and h[8]==cpu[4]and h[11]==cpu[6]and h[12]==3 and cpu[8]&0x400==0,'Genuine FPS CPU/header/DF admission')
    segment=segments[i*40:(i+1)*40];sw=words(segment,0,4);need(sw[0]==i,'Current FPS segment ordinal')
    for j in range(3):
     desc=segment[16+j*8:24+j*8];lo,base_low,base_mid,access,limit_flags,base_hi=struct.unpack('<HHBBBB',desc);base=base_low|(base_mid<<16)|(base_hi<<24);limit=lo|((limit_flags&15)<<16);effective=((limit<<12)|4095)if limit_flags&0x80 else limit
     need(base==0 and access&0x80 and limit_flags&0x40 and effective==0xffffffff and sw[j+1]!=0,'Actual flat32 FPS DS/ES/SS descriptor and complete effective access coverage');counts['actual_FPS_flat_DS_ES_SS_joins']+=1
    pages={p:snap[4820+j*4096:4820+(j+1)*4096]for j,p in enumerate(whole)}
    def actual(address,n):
     p=address&~4095;need(p in pages and(address&4095)+n<=4096,'Actual complete FPS source input extent');return pages[p][address&4095:(address&4095)+n]
    destination,format_,va=h[13:16];need(destination==cpu[6]+0x34 and format_==0x5e1590 and 0x20001000<=va and va+64<=0x20002000,'True source instance destination/physical nonnull fps/actual va_list extent')
    need(actual(format_,16)==snap[529172:529188]and snap[529172:529176]==b'fps\0'and actual(destination,512)==snap[529188:529700]and actual(va,64)==snap[529108:529172],'Full actual argument/input/output bytes joined to own complete source pages')
    if 0x20001000<=h[5] and h[5]+16<=0x20002000:need(actual(h[5],16)==view,'Raw genuine source FS16 view joined to own page')
    else:need(view==bytes(16),'Unmapped source FS head retains explicit empty view')
    if not side:
     need(cpu[9]==fps_identity[1]and words(frame,0,4)==(0x5a2f6e,destination,format_,va),'True FPS cdecl saved return and three actual arguments')
    else:
     entry=fps_pair[-1];a=entry['CPU'];need(cpu[9]==0x5a2f6e and cpu[4]==a[4]+4 and h[5]==entry['header'][5]and list(h[13:16])==entry['header'][13:16],'True FPS cdecl RET before source caller cleanup and same carried hidden FS/args')
     need(all(cpu[j]==a[j]for j in(3,5,6,7))and frame[:12]==bytes.fromhex(entry['frame64_hex'])[4:16],'Actual FPS callee-saved registers and untouched caller argument cells')
     need(fx.hex()==entry['FX512_hex']and env.hex()==entry['ENV28_hex'],'Actual full FPS hardware FP/ENV conservation on current literal-string domain')
     need(cpu[0]==3 and snap[529188:529192]==b'fps\0','Actual finite literal-string formatter return and destination bytes')
     need(snap[529192:529700].hex()==entry['destination512_hex'][8:],'Complete remaining destination tail unchanged by actual finite formatter')
     need(snap[529108:529172].hex()==entry['va_input64_hex'],'Actual literal fps path does not mutate the real va_list backing')
     counts['actual_FPS_cdecl_RET_joins']+=1;counts['actual_FPS_whole_FP_ENV_conservation']+=1;counts['actual_FPS_whole_destination512_joins']+=1
    rp=rawdir/f'fps-{phase}-{i}.bin';rp.write_bytes(snap);pin(rp)
    row=dict(phase=phase,index=i,root=root['root'],side='provider-entry'if not side else'provider-return-before-source-replay',header=list(h),CPU=list(cpu),FX512_hex=fx.hex(),ENV28_hex=env.hex(),frame64_hex=frame.hex(),FS_view16_hex=view.hex(),format_input16_hex=snap[529172:529188].hex(),va_input64_hex=snap[529108:529172].hex(),destination512_hex=snap[529188:529700].hex(),raw_snapshot=str(rp),raw_snapshot_sha256=sha(rp),raw_selectors_hex=segment.hex(),own_source_page_sha256=[hashlib.sha256(pages[p]).hexdigest()for p in whole],own_CRT_page_sha256=[hashlib.sha256(snap[266964+j*4096:266964+(j+1)*4096]).hexdigest()for j in range(64)],raw_source_code_page_hex=snap[724:4820].hex(),CPU_PC_projection='Observer literal named target or source saved continuation, not sampled machine EIP',source_return_replay_observed=False,full_source_model_equivalence=False)
    fps_pair.append(row);fps_events.append(row);counts['actual_FPS_complete_CPU_FX_ENV_frame_sides']+=1;counts['actual_FPS_whole_source_page_sides']+=64;counts['actual_FPS_whole_CRT_page_sides']+=64
   if root['root']==0x40f000:
    need(fcount>0,'Genuine nonnull fps service actually reached')
    fps_domains.append(dict(phase=phase,root=root['root'],instance=0x5fc378,extent=0x4bc,source_object_before_hex=phase_pages['before'][0x5fc000][0x378:0x834].hex(),source_object_after_hex=phase_pages['after'][0x5fc000][0x378:0x834].hex(),actual_object_plus238_before=words(phase_pages['before'][0x5fc000],0x5b0)[0],actual_boundary_sides=fcount,actual_registered_callback=root['callback'],full_reached_source_instruction_trace=False,source_after_seed=False))
