// Private, opt-in actor lifecycle observation. No original logic is replaced.
struct PlatformFp{alignas(16) unsigned char fx[512];PlatformFp(){__asm__ volatile("fxsave64 %0":"=m"(fx)::"memory");}~PlatformFp(){__asm__ volatile("fxrstor64 %0"::"m"(fx):"memory");}};
static bool platform_trace_enabled(){static const bool on=[]{const char*p=std::getenv("MW34_PLATFORM_TRACE");return p&&*p;}();return on;}
FILE*platform_file(){static FILE*f=[]{const char*p=std::getenv("MW34_PLATFORM_TRACE");FILE*r=p&&*p?std::fopen(p,"w"):nullptr;if(p&&*p&&!r)throw std::runtime_error("Platform trace unavailable");return r;}();return f;}
unsigned platform_generation{};std::set<unsigned>platform_parts;unsigned platform_cull_node{};std::map<unsigned,unsigned>platform_aim_counts;
bool platform_loading{};std::map<unsigned,unsigned>platform_actors;std::map<unsigned,unsigned>platform_sampled;
void platform_node(const char*phase,unsigned node){PlatformFp fp;FILE*f=platform_file();if(!f||!node||!readable(node,0x64))return;
 const auto name=pose_name(node,36);if(name.rfind("triturret",0)!=0)return;
 std::fprintf(f,"node phase %s frame %u node %08x name %s flags %08x kind %08x data %08x children %u\n",phase,host.frames,node,name.c_str(),load(node+0x24),load(node+0x34),load(node+0x38),load(node+0x5c));
 const unsigned count=load(node+0x5c),children=load(node+0x60);if(count<=64&&readable(children,count*4))for(unsigned i=0;i<count;++i){const unsigned child=load(children+4*i);if(child&&readable(child,0x64))std::fprintf(f," child node %08x name %s flags %08x kind %08x data %08x\n",child,pose_name(child,36).c_str(),load(child+0x24),load(child+0x34),load(child+0x38));}
 std::fflush(f);
}
void platform_catalog(const char*phase){PlatformFp fp;FILE*f=platform_file();const unsigned list=load(0x5ea6e8);if(!f||!list||!readable(list,4))return;
 std::set<unsigned>seen;for(unsigned e=load(list);e&&readable(e,12)&&seen.insert(e).second&&seen.size()<20000;e=load(e+8))platform_node(phase,load(e));
 std::fprintf(f,"catalog phase %s entries %zu\n",phase,seen.size());std::fflush(f);
}
void platform_actor(const char*phase,unsigned actor){PlatformFp fp;FILE*f=platform_file();auto it=platform_actors.find(actor);if(!f||it==platform_actors.end()||!readable(actor,0x284))return;
 const unsigned weapon=load(actor+0x140),target=load(actor+0x98);unsigned range=0,range2=0,dist2=0;
 if(weapon&&readable(weapon,0x24)){range=load(weapon+0x1c);range2=load(weapon+0x20);}if(target&&readable(target,16))dist2=load(target+12);
 std::fprintf(f,"actor phase %s frame %u actor %08x node %08x name %s active %u weapon %08x rangebits %08x range2bits %08x detectbits %08x basebits %08x target %08x distance2bits %08x\n",phase,host.frames,actor,it->second,pose_name(it->second,36).c_str(),load(actor+8)&255,weapon,range,range2,load(actor+0x148),load(actor+0xa0),target,dist2);std::fflush(f);
}

void platform_shot(const char*phase,unsigned actor,unsigned weapon,unsigned source,unsigned projectile){PlatformFp fp;FILE*f=platform_file();if(!f||!platform_actors.count(actor)||!readable(actor,0x1ac))return;
 const unsigned point=load(actor+0x1a8),player_context=load(0x60861c),player=player_context&&readable(player_context,0x18)?load(player_context+0x14):0;
 std::fprintf(f,"shot phase %s frame %u actor %08x name %s weapon %08x source %08x projectile %08x targetactor %08x player %08x origin",phase,host.frames,actor,pose_name(platform_actors[actor],36).c_str(),weapon,source,projectile,load(actor+0x1a4),player);
 for(unsigned i=0;i<3;++i)std::fprintf(f," %08x",load(actor+0xe0+4*i));std::fprintf(f," muzzle");for(unsigned i=0;i<3;++i)std::fprintf(f," %08x",load(actor+0x16c+4*i));std::fprintf(f," point %08x",point);if(point&&readable(point,12))for(unsigned i=0;i<3;++i)std::fprintf(f," %08x",load(point+4*i));std::fprintf(f,"\n");std::fflush(f);
}
void platform_tree(unsigned node,unsigned depth=0){PlatformFp fp;FILE*f=platform_file();if(!f||!node||depth>6||!readable(node,0x64))return;
 platform_parts.insert(node);std::fprintf(f,"tree frame %u depth %u node %08x name %s flags %08x kind %08x data %08x",host.frames,depth,node,pose_name(node,36).c_str(),load(node+0x24),load(node+0x34),load(node+0x38));
 const unsigned d=load(node+0x38);if(d&&readable(d,0x90)){std::fprintf(f," object");for(unsigned i=0;i<0x90;i+=4)std::fprintf(f," %08x",load(d+i));}std::fprintf(f,"\n");
 unsigned n=load(node+0x5c),a=load(node+0x60);if(n<=64&&readable(a,n*4))for(unsigned i=0;i<n;++i)platform_tree(load(a+i*4),depth+1);std::fflush(f);
}
void platform_aim(const char*phase,unsigned actor){PlatformFp fp;FILE*f=platform_file();if(!f||!platform_actors.count(actor))return;
 std::fprintf(f,"aim phase %s frame %u actor %08x name %s",phase,host.frames,actor,pose_name(platform_actors[actor],36).c_str());
 constexpr unsigned offsets[]={0xfc,0x100,0x104,0x120,0x124,0x128,0x12c,0x158,0x240};for(unsigned a:offsets)std::fprintf(f," field%03x %08x",a,load(actor+a));
 for(unsigned a:{0x100u,0x120u}){unsigned m=load(actor+a);if(m&&readable(m,48)){std::fprintf(f," matrix%03x",a);for(unsigned i=0;i<12;++i)std::fprintf(f," %08x",load(m+i*4));}}std::fprintf(f,"\n");std::fflush(f);
}
void platform_present(){if(!platform_trace_enabled()||host.frames%60)return;platform_player();for(const auto&[actor,node]:platform_actors){platform_actor("present",actor);platform_node("present",node);platform_tree(node);platform_aim("present",actor);}}

void platform_visibility(const char*phase,unsigned target,unsigned node,unsigned result){PlatformFp fp;FILE*f=platform_file();if(!f||!platform_parts.count(node)||!readable(node,0x74))return;
 const unsigned camera=load(0x7402f4),data=load(node+0x38);std::vector<unsigned>words{load(node+0x24),load(node+0x3c),result};for(unsigned i=0;i<4;++i)words.push_back(load(node+0x64+i*4));if(data&&readable(data,0x90))for(unsigned i=0;i<0x90;i+=4)words.push_back(load(data+i));
 using Key=std::tuple<unsigned,unsigned,unsigned,unsigned,std::string>;static std::map<Key,std::vector<unsigned>>last;Key key{platform_generation,target,node,camera,phase};auto it=last.find(key);if(it!=last.end()&&it->second==words&&host.frames%60)return;last[key]=words;
 std::fprintf(f,"visibility phase %s frame %u function %08x camera %08x node %08x name %s result %08x flags %08x mesh %08x bounds",phase,host.frames,target,camera,node,pose_name(node,36).c_str(),result,load(node+0x24),load(node+0x3c));for(unsigned i=0;i<4;++i)std::fprintf(f," %08x",load(node+0x64+i*4));if(data&&readable(data,0x90)){std::fprintf(f," object");for(unsigned i=0;i<0x90;i+=4)std::fprintf(f," %08x",load(data+i));}std::fprintf(f,"\n");std::fflush(f);
}
void platform_player(){PlatformFp fp;FILE*f=platform_file();const unsigned c=load(0x60861c),actor=c&&readable(c,0x18)?load(c+0x14):0,node=actor&&readable(actor,8)?load(actor+4):0,data=node&&readable(node,0x3c)?load(node+0x38):0;if(!f)return;
 std::fprintf(f,"player frame %u actor %08x node %08x data %08x",host.frames,actor,node,data);if(data&&readable(data,0x90)){std::fprintf(f," world");for(unsigned i=0x60;i<0x90;i+=4)std::fprintf(f," %08x",load(data+i));}std::fprintf(f,"\n");std::fflush(f);
}

void*platform_body(State*s,unsigned target,void*p,Body body){
 const unsigned ecx=state.gpr.rcx.dword,edx=state.gpr.rdx.dword,sp=state.gpr.rsp.dword,ret=load(sp);
 if((target==0x4f5910||target==0x4f4ab0||target==0x4eb170||target==0x4fc300)&&platform_parts.count(ecx)){unsigned old=platform_cull_node;platform_cull_node=ecx;try{platform_visibility("enter",target,ecx,edx);void*r=body(s,target,p);platform_visibility("leave",target,ecx,state.gpr.rax.dword);platform_cull_node=old;return r;}catch(...){platform_cull_node=old;throw;}}
 if((target==0x541760||target==0x53d750)&&platform_cull_node){unsigned node=platform_cull_node;void*r=body(s,target,p);platform_visibility("decision",target,node,state.gpr.rax.dword);return r;}
 if(target==0x4a7620&&platform_actors.count(ecx)){platform_actor("retire-enter",ecx);platform_aim("retire",ecx);void*r=body(s,target,p);platform_actor("retire-leave",ecx);return r;}
 if(target==0x4a71c0&&platform_actors.count(ecx)){const bool sample=platform_aim_counts[ecx]++<10||host.frames%60==0;if(sample)platform_aim("before",ecx);void*r=body(s,target,p);if(sample)platform_aim("after",ecx);return r;}
 if(target==0x4b4a40){const unsigned actor=state.gpr.rsi.dword;const bool shot=ret==0x4a6fd8&&platform_actors.count(actor);if(shot)platform_shot("attempt",actor,ecx,edx,0);void*r=body(s,target,p);if(shot)platform_shot(state.gpr.rax.dword?"accepted":"rejected",actor,ecx,edx,state.gpr.rax.dword);return r;}

 if(target==0x4a76b0){const bool old=platform_loading;if(!old){platform_actors.clear();platform_sampled.clear();platform_parts.clear();platform_aim_counts.clear();++platform_generation;}platform_loading=true;try{platform_catalog("before-loader");void*r=body(s,target,p);platform_catalog("after-loader");for(const auto&[actor,node]:platform_actors)platform_actor("after-loader",actor);platform_loading=old;return r;}catch(...){platform_loading=old;throw;}}
 if(target==0x4a5c60){const unsigned node=load(sp+4);platform_node("constructor",node);if(pose_name(node,36).rfind("triturret",0)==0)platform_actors[ecx]=node;void*r=body(s,target,p);platform_actor("constructed",ecx);return r;}
 if(target==0x4f8b80){const std::string query=ecx?pose_name(ecx,64):"next";void*r=body(s,target,p);const unsigned node=state.gpr.rax.dword;
  if(platform_loading){PlatformFp fp;std::fprintf(platform_file(),"enumerator frame %u query %s category %u ret %08x result %08x name %s\n",host.frames,query.c_str(),edx,ret,node,pose_name(node,36).c_str());std::fflush(platform_file());platform_node("enumerated",node);}return r;}
 if(target==0x4f9d60){const std::string name=pose_name(ecx,36);void*r=body(s,target,p);if(name.rfind("triturret",0)==0){PlatformFp fp;const unsigned child=state.gpr.rax.dword;std::fprintf(platform_file(),"healthy-lookup frame %u node %08x name %s result %08x childname %s flags %08x\n",host.frames,ecx,name.c_str(),child,pose_name(child,36).c_str(),child&&readable(child,0x28)?load(child+0x24):0);std::fflush(platform_file());}return r;}
 if(target==0x4d7330){const std::string name=pose_name(ecx,64);void*r=body(s,target,p);if(name.rfind("triturret",0)==0){PlatformFp fp;std::fprintf(platform_file(),"objective-lookup frame %u name %s result %08x\n",host.frames,name.c_str(),state.gpr.rax.dword);std::fflush(platform_file());}return r;}
 if(target==0x4d6d00){void*r=body(s,target,p);platform_actor("range-init",ecx);return r;}
 void*r=body(s,target,p);if(target==0x4a7ab0&&platform_actors.count(ecx)&&(!platform_sampled.count(ecx)||host.frames-platform_sampled[ecx]>=60)){platform_sampled[ecx]=host.frames;platform_actor(state.gpr.rax.dword?"range-eligible":"range-ineligible",ecx);}return r;
}
