// Optional uncapped-timing repair at the original turret aim boundary.
// Keep the original helper ABI, table initialization and transform publication.
struct TurretAimFp {
 alignas(16) unsigned char fx[512];DWORD error{};
 TurretAimFp(){__asm__ volatile("fxsave64 %0":"=m"(fx)::"memory");error=::GetLastError();}
 ~TurretAimFp(){::SetLastError(error);__asm__ volatile("fxrstor64 %0"::"m"(fx):"memory");}
};
struct TurretAimScope {
 unsigned actor{},node{},matrix{},dt_bits{};
 mw34::turret_aim::YawBits yaw{};
};
TurretAimScope turret_aim_scope;
bool turret_aim_on(){static const bool value=[]{const char*p=std::getenv("MW34_TURRET_AIM_REPAIR");return p&&std::strcmp(p,"1")==0;}();return value;}
bool turret_aim_logging(){static const bool value=[]{const char*p=std::getenv("MW34_TURRET_AIM_LOG");return p&&*p;}();return value;}
FILE*turret_aim_log(){static FILE*f=[]{const char*p=std::getenv("MW34_TURRET_AIM_LOG");if(!p||!*p)return static_cast<FILE*>(nullptr);FILE*r=std::fopen(p,"w");if(!r)throw std::runtime_error("Turret aim log unavailable");return r;}();return f;}
float turret_aim_float(unsigned bits){float f;std::memcpy(&f,&bits,4);return f;}
mw34::turret_aim::YawBits turret_aim_yaw(unsigned matrix){return {load(matrix),load(matrix+8),load(matrix+0x18),load(matrix+0x20)};}
TurretAimScope turret_aim_capture(unsigned actor){
 TurretAimFp preserve;mw34::vkscene::HostFpEnvironment fp;
 TurretAimScope scope;
 if(!actor||!readable(actor,0x284)||load(actor)!=0x5c8770)return scope;
 const unsigned node=load(actor+0xfc),matrix=load(actor+0x100);
 if(!node||!readable(node,0x3c)||load(node+0x34)!=5)return scope;
 const unsigned data=load(node+0x38);
 if(!data||!readable(data,0x60)||matrix!=data+0x30)return scope;
 scope={actor,node,matrix,load(0x72c52c),turret_aim_yaw(matrix)};
 return scope;
}
void turret_aim_lookup_return(State*s,unsigned input_bits){
 TurretAimFp preserve;mw34::vkscene::HostFpEnvironment fp;
 auto*top=s->st.elems[0].val.data;
 std::uint64_t significand;unsigned short exponent;
 std::memcpy(&significand,top,8);std::memcpy(&exponent,top+8,2);
 const bool one=significand==0x8000000000000000ULL&&exponent==0x3fff;
 const float x=turret_aim_float(input_bits);
 const auto result=mw34::turret_aim::first_interval(x,one?1.f:0.f,wide_float(0x63d340),wide_float(0x63d344));
 const bool applied=turret_aim_on()&&one&&result.changed;
 if(applied){const auto encoded=mw34::turret_aim::encode_f32(result.value);std::memcpy(top,encoded.data(),encoded.size());}
 if(FILE*f=turret_aim_log();f&&(one||host.frames%60==0)){
  std::fprintf(f,"lookup frame %u actor %08x dt-bits %08x input %.9g original-one %u candidate %.9g applied %u\n",host.frames,turret_aim_scope.actor,turret_aim_scope.dt_bits,double(x),unsigned(one),double(result.value),unsigned(applied));std::fflush(f);
 }
}
void turret_aim_publish(unsigned node,unsigned matrix,unsigned caller){
 const auto&scope=turret_aim_scope;
 if(!scope.actor||caller!=0x4a7426||node!=scope.node||matrix!=scope.matrix||
    load(scope.actor+0xfc)!=node||load(scope.actor+0x100)!=matrix)return;
 TurretAimFp preserve;mw34::vkscene::HostFpEnvironment fp;
 const auto current=turret_aim_yaw(matrix);
 const bool collapsed=mw34::turret_aim::collapsed_yaw(current);
 const bool keep=mw34::turret_aim::should_keep_yaw(turret_aim_float(scope.dt_bits),scope.yaw,current);
 const bool applied=turret_aim_on()&&keep;
 if(applied){constexpr unsigned offsets[]={0,8,0x18,0x20};for(unsigned i=0;i<4;++i)store(matrix+offsets[i],scope.yaw[i]);}
 if(FILE*f=turret_aim_log();f&&(collapsed||applied||host.frames%60==0)){
  std::fprintf(f,"publish frame %u actor %08x node %08x dt-bits %08x collapsed %u applied %u yaw",host.frames,scope.actor,node,scope.dt_bits,unsigned(collapsed),unsigned(applied));for(unsigned v:current)std::fprintf(f," %08x",v);std::fprintf(f,"\n");std::fflush(f);
 }
}
template<class Next>void*turret_aim_body(State*s,unsigned target,void*p,Next&&next){
 if(!turret_aim_on()&&!turret_aim_logging())return next();
 if(target==0x4a71c0){
  const auto previous=turret_aim_scope;turret_aim_scope=turret_aim_capture(state.gpr.rcx.dword);
  try{void*r=next();turret_aim_scope=previous;return r;}catch(...){turret_aim_scope=previous;throw;}
 }
 if(turret_aim_scope.actor&&target==0x523f70){
  const unsigned sp=state.gpr.rsp.dword;
  if(readable(sp,8)&&load(sp)==0x4a729b){const unsigned input=load(sp+4);void*r=next();turret_aim_lookup_return(s,input);return r;}
 }
 if(turret_aim_scope.actor&&target==0x4fc300)turret_aim_publish(state.gpr.rcx.dword,state.gpr.rdx.dword,load(state.gpr.rsp.dword));
 return next();
}
