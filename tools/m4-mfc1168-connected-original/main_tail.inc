    // The accepted full130 template above supplies the identical sparse image,
    // actual preferred DLL loader, empty CRT registry and eight producer shims.
    // None of its unrelated FS/NULL/vtable/Lockit/formatter hooks are installed.
    owner=GetCurrentThreadId();mw34::capture_direct::Writer out(argv[4]);connected_writer=&out;
    Header header{};std::memcpy(header.magic,"MW4M131P",8);header.version=1;header.sequence_count=sequences;header.root_count=roots;header.total_phases=phase_count;header.page_count=observed_page_count;header.record_size=sizeof(Record);out.append("header.bin",&header,sizeof(header));
    out.append("crt-image.bin",crtbytes.data(),crtbytes.size());out.append("crt-api-targets.bin",registry_API_targets,sizeof(registry_API_targets));out.append("mfc-image.bin",mfcbytes.data(),mfcbytes.size());
    for(unsigned k=0;k<5;++k)out.append("lockit/post-DllMain/"+std::to_string(lockit_bootstrap_bases[k])+"-page.bin",lockit_bootstrap_pages[k],4096);
    // Exact named/ordinal owning game imports, established without invoking them.
    const auto service=GetProcAddress(mfc,reinterpret_cast<LPCSTR>(1168)),mbcp=GetProcAddress(crt,"_setmbcp");require(reinterpret_cast<unsigned>(service)==0x5f401083&&reinterpret_cast<unsigned>(mbcp)==0x78003ddb,"Physical current1168 and setmbcp exports");require(dword(0x5bb210)==0x80000490,"Physical game ordinal1168 import");*reinterpret_cast<unsigned*>(0x5bb210)=reinterpret_cast<unsigned>(service);*reinterpret_cast<unsigned*>(0x5bb674)=reinterpret_cast<unsigned>(mbcp);
    const std::array<unsigned,6>owning{0x5bb210,reinterpret_cast<unsigned>(service),reinterpret_cast<unsigned>(mfc),0x5bb674,reinterpret_cast<unsigned>(mbcp),reinterpret_cast<unsigned>(crt)};dump("loaded/owning-game-imports.bin",owning.data(),sizeof(owning));
    const unsigned sequence=0,repeat=0,cw=0x007f,top=0;
    // Same first finite caller domain as the accepted original130 schedule.
    // The producer's actual FX/ENV and all guest memory remain carried.
    for(unsigned i=0;i<pages.size();++i)if(page_permissions[i]==2)std::memcpy(pages[i],pack.data()+12+i*4104+8,page_size);
    // Writable reset includes the owning source IAT page; reapply its actual
    // loader identities exactly as the accepted original130 per-sequence setup.
    *reinterpret_cast<unsigned*>(0x5bb4f8)=reinterpret_cast<unsigned>(cpctor);*reinterpret_cast<unsigned*>(0x5bb4f4)=reinterpret_cast<unsigned>(cpdtor);
    *reinterpret_cast<unsigned*>(0x5bb52c)=reinterpret_cast<unsigned>(original_onexit);*reinterpret_cast<unsigned*>(0x5bb530)=reinterpret_cast<unsigned>(original_dllonexit);*reinterpret_cast<unsigned*>(0x5bb670)=reinterpret_cast<unsigned>(original_strdup);*reinterpret_cast<unsigned*>(0x5bb4bc)=reinterpret_cast<unsigned>(mfc823);*reinterpret_cast<unsigned*>(0x5bb454)=reinterpret_cast<unsigned>(mfc540);*reinterpret_cast<unsigned*>(0x5bb4c8)=reinterpret_cast<unsigned>(mfc825);*reinterpret_cast<unsigned*>(0x5bb6dc)=reinterpret_cast<unsigned>(&spi_service_entry);*reinterpret_cast<unsigned*>(0x5bb210)=reinterpret_cast<unsigned>(service);*reinterpret_cast<unsigned*>(0x5bb674)=reinterpret_cast<unsigned>(mbcp);
    mixed_input={0x13579bdf,0x2468ace0,0x81726354,0x10293847,frame,0x92837465,0x56473829,0xaabbccdd,0x202,entries[0]};std::memset(mixed_guest_fx,0,512);const auto cw16=static_cast<unsigned short>(cw);std::memcpy(mixed_guest_fx,&cw16,2);const unsigned mxcsr=0x1f80;std::memcpy(mixed_guest_fx+24,&mxcsr,4);mixed_env_ready=0;
    auto*sentinel_end=reinterpret_cast<unsigned char*>(0x5ac3ec);protect(reinterpret_cast<void*>(0x5ac000),PAGE_EXECUTE_READWRITE);sentinel_end[0]=0xe9;const auto sentinel_delta=capture_pc-(0x5ac3ec+5);std::memcpy(sentinel_end+1,&sentinel_delta,4);protect(reinterpret_cast<void*>(0x5ac000),PAGE_EXECUTE_READ);require(FlushInstructionCache(GetCurrentProcess(),sentinel_end,5),"Sentinel terminal cache");
    mixed_input.pc=0x5ac3d8;std::memcpy(reinterpret_cast<void*>(frame),&capture_pc,4);require(execute()==0&&dword(0x9a17ec)==0xffffffff&&dword(0x9a17f0)==0xffffffff,"Actual carried source sentinel effects");std::memcpy(mixed_guest_fx,mixed_fx_after,512);std::memcpy(mixed_guest_env,mixed_env_after,28);mixed_env_ready=1;
    mixed_input=mixed_after;mixed_input.esp=frame;mixed_input.pc=0x78004482;std::memcpy(reinterpret_cast<void*>(frame),&capture_pc,4);require(execute()==0&&mixed_after.pc==capture_pc&&mixed_after.esp==frame+4&&*crtbegin&&*crtnext==*crtbegin&&dword(*crtbegin)==0,"Actual authentic registry producer");
    require(!fs_error&&registry_API_count<=256,"Bounded producer ledger before export");out.append("bootstrap/0/producer-after-cpu.bin",&mixed_after,40);out.append("bootstrap/0/producer-after-fx.bin",mixed_fx_after,512);out.append("bootstrap/0/producer-after-env.bin",mixed_env_after,28);out.append("bootstrap/0/producer-api-count.bin",&registry_API_count,4);out.append("bootstrap/0/producer-api-ledger.bin",registry_API_ledger,registry_API_count*sizeof(RegistryAPIEntry));
    for(unsigned i=0;i<registry_API_count;++i)if(registry_API_ledger[i].kind==0&&registry_API_ledger[i].after.eax){require(registry_initial_sizes[i]&&registry_initial_sizes[i]<=1024,"Actual producer initial capacity");const auto s="bootstrap/0/producer-api-initial/"+std::to_string(i);out.append(s+"/size.bin",&registry_initial_sizes[i],4);out.append(s+"/bytes.bin",registry_initial_bytes[i],registry_initial_sizes[i]);}
    std::memcpy(mixed_guest_fx,mixed_fx_after,512);std::memcpy(mixed_guest_env,mixed_env_after,28);mixed_env_ready=1;
    mixed_input={0x13579bdf,0x2468ace0,0x81726354,0x10293847,frame,0x92837465,0x56473829,0xaabbccdd,0x202,entries[0]};
    constexpr std::array<unsigned,3>extras{0x5cd000,0x5e3000,0x5e9000};
    const auto registry_snapshot=[&](const std::string&stem){const auto actual_heap=*reinterpret_cast<HANDLE*>(0x78035000);const auto cap=HeapSize(actual_heap,0,reinterpret_cast<void*>(*crtbegin));require(cap!=SIZE_T(-1)&&cap<=512&&*crtnext>=*crtbegin&&*crtnext-*crtbegin<=cap,"Actual current full registry backing");const std::array<unsigned,5>meta{*crtbegin,*crtnext,static_cast<unsigned>(cap),dword(0x78035004),reinterpret_cast<unsigned>(actual_heap)};out.append(stem+"/meta.bin",meta.data(),sizeof(meta));out.append(stem+"/bytes.bin",reinterpret_cast<void*>(*crtbegin),cap);};
    for(unsigned phase=0;phase<entries.size();++phase){
        if(phase){mixed_input=mixed_after;std::memcpy(mixed_guest_fx,mixed_fx_after,512);std::memcpy(mixed_guest_env,mixed_env_after,28);mixed_env_ready=1;}
        mixed_input.esp=frame;mixed_input.pc=entries[phase];std::memcpy(reinterpret_cast<void*>(frame),&capture_pc,4);
        const auto stem="phase/0/"+std::to_string(phase);registry_snapshot(stem+"/registry-before");
        const bool mfc_phase=phase==13;if(mfc_phase){registry_cleanup.restore();connected_named_identity();module_pages("BEFORE/MFC",0x5f400000,0xd0000);module_pages("BEFORE/CRT",0x78000000,0x40000);domain("BEFORE/domain");connected_lock("BEFORE/CRT-codepage-lock");}
        auto r=std::make_unique<Record>();r->tag={sequence,repeat,phase,table_slots[phase],entries[phase],cw,top,0,0};copy_pages(r->memory_before);
        for(auto page:extras)out.append(stem+"/extra-before/"+std::to_string(page)+".bin",reinterpret_cast<void*>(page),4096);out.append(stem+"/stack-before.bin",reinterpret_cast<void*>(0x20001000),4096);
        if(mfc_phase){named_IAT(true);connected_patch_sources(true);}
        registry_API_count=0;fs_error=0;std::memset(registry_API_ledger,0,sizeof(registry_API_ledger));mixed_before={};mixed_after={};r->tag.status=execute();
        copy_capture(*r);r->tag.host_restored=host_restored(*r)?1U:0U;
        if(mfc_phase){named_IAT(false);connected_patch_sources(false);}
        copy_pages(r->memory_after);registry_snapshot(stem+"/registry-after");
        for(auto page:extras)out.append(stem+"/extra-after/"+std::to_string(page)+".bin",reinterpret_cast<void*>(page),4096);out.append(stem+"/stack-after.bin",reinterpret_cast<void*>(0x20001000),4096);
        const auto actual_heap=*reinterpret_cast<HANDLE*>(0x78035000);const auto cap=HeapSize(actual_heap,0,reinterpret_cast<void*>(*crtbegin));r->registry_begin=*crtbegin;r->registry_next=*crtnext;r->registry_mode=dword(0x78035004);r->registry_capacity=static_cast<unsigned>(cap);std::memcpy(r->registry_bytes.data(),reinterpret_cast<void*>(*crtbegin),cap);
        require(registry_API_count<=256,"Bounded phase API ledger before export");out.append(stem+"/api-count.bin",&registry_API_count,4);out.append(stem+"/api-ledger.bin",registry_API_ledger,registry_API_count*sizeof(RegistryAPIEntry));
        out.append(stem+"/TEB-before-base.bin",&mixed_teb_before_base,4);out.append(stem+"/TEB-before.bin",mixed_teb_before_pages,8192);out.append(stem+"/TEB-after-base.bin",&mixed_teb_after_base,4);out.append(stem+"/TEB-after.bin",mixed_teb_after_pages,8192);out.append(stem+".bin",r.get(),sizeof(*r));
        if(mfc_phase){dump("boundaries/count.bin",&boundary_count,4);dump("boundaries/records.bin",boundaries,boundary_count*sizeof(Boundary));dump("named-API/count.bin",&named_count,4);dump("named-API/records.bin",named_boundaries,named_count*sizeof(NamedBoundary));module_pages("AFTER/MFC",0x5f400000,0xd0000);module_pages("AFTER/CRT",0x78000000,0x40000);domain("AFTER/domain");connected_lock("AFTER/CRT-codepage-lock");}
        if(r->tag.status||!r->tag.host_restored||r->after.pc!=capture_pc||r->after.esp!=returned_esp||fs_error||observer_error){out.finish();std::cerr<<"Genuine chronological prefix failed phase="<<phase<<" status="<<r->tag.status<<" observer="<<observer_error<<" FS="<<fs_error<<'\n';return 1;}
    }
    // Restore exact owning API cells before research registry cleanup. Borrowed
    // manager/thread/global objects and DLL lock remain owned by their DLLs.
    registry_cleanup.restore();for(const auto&span:code_bindings){const auto&origin=span.origin?provider:image;require(!std::memcmp(reinterpret_cast<void*>(span.pc),origin.data()+span.image_offset,span.size),"Complete selected physical source restored after normal observations");}
    registry_snapshot("cleanup/0/registry");original_free(reinterpret_cast<void*>(*crtbegin));*crtbegin=0;*crtnext=0;
    dump("COMPLETE.txt","complete",8);out.finish();connected_writer=nullptr;std::cout<<"one chronological13-root prefix plus genuine1168 completed; semantic/native acceptance pending\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
