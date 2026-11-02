// Included inside Stage. Controller values enter the original action/analog services,
// never the OS keyboard queue or physics/weapon state.
struct ControllerFp {
    alignas(16) unsigned char fx[512]; DWORD error{};
    ControllerFp(){__asm__ volatile("fxsave64 %0":"=m"(fx)::"memory");error=::GetLastError();}
    ~ControllerFp(){::SetLastError(error);__asm__ volatile("fxrstor64 %0"::"m"(fx):"memory");}
};
std::unique_ptr<mw34::controller::Input> controller;
bool controller_checked{},controller_throttle_owned{},controller_in_callback{};
std::set<unsigned> controller_temporary_modes;
FILE*controller_trace(){static FILE* f=[]{const wchar_t* path=::_wgetenv(L"MW34_CONTROLLER_LOG");if(!path||!*path)return static_cast<FILE*>(nullptr);FILE* out=::_wfopen(path,L"w");if(!out)throw std::runtime_error("Controller trace could not open");return out;}();return f;}
bool controller_requested()const {static const bool requested=[]{const wchar_t* p=::_wgetenv(L"MW34_CONTROLLER_CONFIG");return p&&*p;}();return requested;}
void controller_initialize() {
    if(controller_checked)return;
    ControllerFp preserve;mw34::vkscene::HostFpEnvironment fp;
    controller_checked=true;
    const wchar_t* config=::_wgetenv(L"MW34_CONTROLLER_CONFIG");if(!config||!*config)return;
    const wchar_t* sdl=::_wgetenv(L"MW34_CONTROLLER_SDL");if(!sdl||!*sdl)throw std::runtime_error("Controller SDL3 path missing");
    controller=std::make_unique<mw34::controller::Input>(config,sdl);
}
bool controller_focus() {
    const HWND foreground=::GetForegroundWindow();DWORD process{};
    if(foreground)::GetWindowThreadProcessId(foreground,&process);
    return foreground&&process==::GetCurrentProcessId();
}
void controller_poll() {
    ControllerFp preserve;mw34::vkscene::HostFpEnvironment fp;
    controller_initialize();if(!controller)return;
    controller->poll(controller_focus()&&!photo_replay_consume_input(),host.frames);
    if(FILE* f=controller_trace();f&&host.frames%60==0){std::fprintf(f,"poll %u connected %u armed %u\n",host.frames,unsigned(controller->state.connected),unsigned(controller->state.armed));std::fflush(f);}
}
void controller_dispatch() {
    if(!controller||controller_in_callback)return;
    ControllerFp preserve;mw34::vkscene::HostFpEnvironment fp;
    const unsigned manager=load(0x63cdb8);
    if(!manager||!readable(manager,0x3f5c)||!runtime.memory().load<unsigned char>({manager+0x3f58}))return;
    // Original 51C420 validates/uses the active context's command callback table.
    // Preserve every caller register/x87 slot around this additional provider callback.
    const State saved=state;controller_in_callback=true;
    try {
        for(unsigned command=1;command<167;++command)if(controller->state.pressed[command]){
            if(command>=load(manager+4))throw std::runtime_error("Controller action exceeds active command table");
            state.gpr.rcx.dword=command;
            const unsigned result=call_guest(0x51c440,{},false,"modern controller command");
            if(FILE* f=controller_trace()){std::fprintf(f,"command %u id %u dispatched %u\n",host.frames,command,result);std::fflush(f);}
            state=saved;
        }
    }catch(...){state=saved;controller_in_callback=false;throw;}
    controller_in_callback=false;
}
template<class Next>void*controller_body(State*s,unsigned target,void*p,Next&&next) {
    if(target==0x51b360&&headlight_enabled()&&
       (frontend_on()||photo_replay_consume_input()||headlight_world_frame==~0U||host.frames-headlight_world_frame>1))headlight_input(false);
    if(!controller_requested()||controller_in_callback)return next();
    if(target==0x51b360){controller_poll();void* r=next();controller_dispatch();return r;}
    if(target==0x51c370){
        const unsigned sp=state.gpr.rsp.dword,manager=state.gpr.rcx.dword;
        if(!readable(sp,8)||!readable(manager+0x3f58,1))deny("Controller action query outside memory contract",sp);
        const unsigned command=load(sp+4);const bool enabled=runtime.memory().load<unsigned char>({manager+0x3f58})!=0;
        void* r=next();
        if(controller&&enabled&&command<167){
            if((command==24||command==25)&&(state.gpr.rax.dword&3))controller_throttle_owned=false;
            state.gpr.rax.dword|=controller->state.actions[command];
            if(command==61){static unsigned last=~0U;const unsigned value=state.gpr.rax.dword;if(last!=value){last=value;ControllerFp preserve;mw34::vkscene::HostFpEnvironment fp;if(FILE* f=controller_trace()){std::fprintf(f,"fire-query %u value %u\n",host.frames,value);std::fflush(f);}}}
        }
        return r;
    }
    // Player input update scopes: restore only the temporary absolute-throttle mode.
    // Keyboard throttle code can still clear the mode and take ownership during the update.
    if(target==0x427d60||target==0x46b0a0){
        const unsigned receiver=state.gpr.rcx.dword;
        const unsigned base=target==0x427d60?receiver-0x14c:receiver;
        if(!readable(base+0x3c,1)||!writable(base+0x3c,1))deny("Controller input owner outside memory contract",base);
        const unsigned char before=runtime.memory().load<unsigned char>({base+0x3c});
        try{void* r=next();if(controller_temporary_modes.erase(base)&&!before&&runtime.memory().load<unsigned char>({base+0x3c})==1)runtime.memory().store<unsigned char>({base+0x3c},0);return r;}
        catch(...){if(controller_temporary_modes.erase(base))runtime.memory().store<unsigned char>({base+0x3c},before);throw;}
    }
    if(target==0x427870||target==0x46af30){
        const unsigned owner=state.gpr.rcx.dword,sp=state.gpr.rsp.dword;
        if(!readable(sp,24))deny("Controller analog arguments outside memory contract",sp);
        const std::array<unsigned,4> outputs{load(sp+8),load(sp+12),load(sp+20),load(sp+16)};
        void* r=next();
        if(controller){
            ControllerFp preserve;mw34::vkscene::HostFpEnvironment fp;
            const auto& sample=controller->state;
            if(sample.connected&&sample.analog[0]!=0)controller_throttle_owned=true;
            for(unsigned i=0;i<4;++i){
                if(!readable(outputs[i],4)||!writable(outputs[i],4))deny("Controller analog output outside memory contract",outputs[i]);
                if(i==0&&controller_throttle_owned){
                    if(!writable(owner+0x3c,1))deny("Controller throttle mode outside memory contract",owner);
                    runtime.memory().store<unsigned char>({owner+0x3c},1);
                    controller_temporary_modes.insert(owner);
                    wide_store_float(outputs[i],float(sample.analog[i]));
                } else if(i>0&&sample.connected&&sample.analog[i]!=0)
                    wide_store_float(outputs[i],float(std::clamp(double(wide_float(outputs[i]))+sample.analog[i],-1.,1.)));
            }
            if(FILE* f=controller_trace();f&&host.frames%60==0){std::fprintf(f,"analog %u helper %08x owned %u values %.6f %.6f %.6f %.6f\n",host.frames,target,unsigned(controller_throttle_owned),double(wide_float(outputs[0])),double(wide_float(outputs[1])),double(wide_float(outputs[2])),double(wide_float(outputs[3])));std::fflush(f);}
        }
        return r;
    }
    return next();
}
