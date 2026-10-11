            def fps_boundary(model,fact):
                CPU(model,fact['CPU'],'Literal full FPS CPU '+str((phase,fact['index'])))
                eq(model.fx.hex(),fact['FX512_hex'],'Whole literal FPS FX512');eq(env[0].hex(),fact['ENV28_hex'],'Whole literal FPS ENV28');eq(model.bytes(model.reg('esp'),64).hex(),fact['frame64_hex'],'Whole source-derived true FPS cdecl frame64')
                eq(model.bytes(0x7ffde000,4),struct.pack('<I',fact['header'][5]),'Literal carried FPS hidden FS head')
                s=raw(fact['raw_snapshot'],fact['raw_snapshot_sha256']);stack=model.bytes(0x20001000,4096);actual_stack=s[4820+whole.index(0x20001000)*4096:4820+(whole.index(0x20001000)+1)*4096]
                for i,(a,b)in enumerate(zip(stack,actual_stack)):
                    if a!=b:dead_stack.append(dict(boundary_role='FPS',boundary_index=fact['index'],address=0x20001000+i,source_value=a,actual_value=b,source_access_index=len(model.accesses),value_seeded=False))
                for j,p in enumerate(whole):
                    if p==0x20001000:continue
                    eq(model.bytes(p,4096),s[4820+j*4096:4820+(j+1)*4096],'Whole literal FPS source page '+hex(p));counts['literal_FPS_whole_nonstack_pages']+=1
                for j,p in enumerate(range(0x78000000,0x78040000,4096)):
                    eq(model.bytes(p,4096),s[266964+j*4096:266964+(j+1)*4096],'Whole literal FPS CRT page '+hex(p));counts['literal_FPS_whole_CRT_pages']+=1
                destination,format_,va=fact['header'][13:16]
                eq(model.bytes(destination,512).hex(),fact['destination512_hex'],'Complete literal FPS destination512');eq(model.bytes(format_,16).hex(),fact['format_input16_hex'],'Complete source FPS format16');eq(model.bytes(va,64).hex(),fact['va_input64_hex'],'Complete literal FPS real va_list64')
                if fact['index']:
                    counts['literal_FPS_provider_instructions']=sum(0x78000000<=p<0x78040000 for p in model.PCs)
                    eq(s[724:4820],raw(fpsfacts[0]['raw_snapshot'],fpsfacts[0]['raw_snapshot_sha256'])[724:4820],'Whole separately observed FPS5A2000 page carried; not a model seed')
                join=dict(phase=phase,index=fact['index'],source_access_index=len(model.accesses),source_CPU=list(model.projected_cpu()),undefined_flags=dict(undefined),complete_source_nonstack_pages=63,complete_CRT_pages=64,whole_frame64=True,whole_destination512=True,whole_format16=True,whole_va64=True,provider_CPU_or_output_seed=False)
                FPS_joins.append(join);counts['literal_FPS_CPU_FX_ENV_frame_joins']+=1
