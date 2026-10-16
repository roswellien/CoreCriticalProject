// Development-only partial removal of original perspective iterations. The
// original last iteration retains machine state; unowned scratch reads stop.
struct ProjectionToken {unsigned count{},frame{},mesh{},polygon{},descriptor{},device{},texture{},material{};std::shared_ptr<const mw34::vkscene::ModelInstance> instance;};
std::optional<ProjectionToken> projection_token;
mw34::projection::Dirty projection_dirty;
unsigned projection_host_copy{};
std::uint64_t projection_candidates{},projection_skipped{},projection_consumed{},projection_depth_copies{},projection_semantic=0xcbf29ce484222325ULL,projection_commands{};
std::ofstream projection_log;
std::array<std::uint64_t,16> projection_rejected{};std::uint64_t projection_calls{};
unsigned projection_reject(unsigned reason){if(++projection_rejected[reason]==1)std::fprintf(stderr,"Projection gate rejected reason %u pc %08x frame %u\n",reason,state.gpr.rip.dword,host.frames);return 0;}
static unsigned projection_mode(){static unsigned mode=[]{const char*p=std::getenv("MW34_GPU_PROJECTION");if(!p||!std::strcmp(p,"0"))return 0U;if(!std::strcmp(p,"1"))return 1U;if(!std::strcmp(p,"2"))return 2U;throw std::runtime_error("MW34_GPU_PROJECTION must be 0, 1 (reference), or 2 (prefix bypass)");}();return mode;}
void projection_access(unsigned address,unsigned size,unsigned write,const State*observed_state=nullptr){
 if(!mw34::projection::overlaps(address,size))return;
 const unsigned offset=(address-mw34::projection::scratch)%32,pc=(observed_state?observed_state:&state)->gpr.rip.dword;
 const bool token_range=projection_token&&address>=mw34::projection::scratch&&std::uint64_t(address)+size<=std::uint64_t(mw34::projection::scratch)+32*projection_token->count;
 if(write){const bool copy=token_range&&(pc==0x57d6d4||pc==0x57d6ed)&&size==4&&offset==12;
  const bool dirty=copy&&projection_dirty.any(address-4,4);projection_dirty.set(address,size,dirty);return;}
 if(projection_host_copy||!projection_dirty.any(address,size))return;
 if(token_range&&(pc==0x57d6ce||pc==0x57d6e7)&&size==4&&offset==8){++projection_depth_copies;return;}
 throw std::runtime_error("Unowned read of omitted projection scratch: address="+std::to_string(address)+" pc="+std::to_string(pc));
}
bool projection_ftol_owned(){
 const unsigned cell=0x5bb644,raw=load(cell);
 const Import*source=host.by_game_raw(cell);
 const Body expected=ftol_fast_on()?&ftol_body:&mw34_attach_m_78002551_body;
 return load(0x5ac340)==0xb64425ffU&&load(0x5ac342)==0x005bb644U&&!writable(0x5ac340,6)&&
  source&&game_import(raw)==source&&source->cell==cell&&same(source->dll,"MSVCRT.dll")&&source->name=="_ftol"&&
  source->bound==0x78002551&&!find(raw)&&!writable(cell,4)&&find(source->bound)==expected;
}
unsigned projection_begin(){
 if(!projection_mode())return 0;++projection_calls;if(state.gpr.rip.dword!=0x540977||!world_scope||frontend_on()||override_suppress_draw())return projection_reject(0);
 if(projection_token)throw std::runtime_error("Nested pending GPU projection token");
 if(std::getenv("MW34_DIVERGENCE_TRACE"))throw std::runtime_error("Raw TL diagnostic capture is incompatible with projection bypass");
 const auto&scope=*world_scope;const unsigned frame=scope.frame_base,n=state.gpr.rcx.dword;
 if(n<3||n>128||frame!=state.gpr.rbp.dword||!readable(frame-0x120,0x124)||load(frame-0x38)!=scope.mesh)return projection_reject(1);
 if(!load(frame-0xc)||load(frame-0x14)||load(frame-0x54)||load(frame-0x74)&0x3f||load(0x7489a8)||load(0x74a268)||load(0x74a26c)!=0x3f800000||load(0x72f3c8)!=0x57d690||!projection_ftol_owned()){if(!projection_rejected[2])std::fprintf(stderr,"Projection gate flags %08x %08x %08x layers %08x mode %08x alpha %08x cb %08x ftol %08x\n",load(frame-8),load(frame-0x54),load(frame-0x74),load(0x7489a8),load(0x74a268),load(0x74a26c),load(0x72f3c8),load(0x5bb644));return projection_reject(2);}
 const unsigned address=load(frame-0x34);auto slot=mw34::world::polygon_slot(scope.polygon_base,scope.polygon_lookup->size(),address);if(!slot)return 0;
 const int index=(*scope.polygon_lookup)[*slot];if(index<0)return 0;const auto&polygon=(*scope.polygons)[size_t(index)];
 const unsigned material=load(frame-0x44);
 if(polygon.source!=address||polygon.material!=material||polygon.corners.size()!=n||!polygon.resident||!readable(material,0x14)||!(load(material)&0x100)||(polygon.flags&0x400)||load(address+4))return 0;
 const unsigned link=load(material+0x10);if(!link||!readable(link,8))return 0;const unsigned descriptor=load(link+4);if(!descriptor||!readable(descriptor,0x18)||load(descriptor+0xc)==4)return 0;
 auto*dev=device(load(0x809370));if(!dev||!dev->in_scene||!host.sren||!mw34::vkscene::Renderer::gpu_models()||dev->rs[D3DRENDERSTATE_ALPHABLENDENABLE]||dev->rs[D3DRENDERSTATE_ALPHATESTENABLE])return 0;
 if(reinterpret_cast<const unsigned char*>(&state)[2745]!=1)return 0;
 for(unsigned address_: {0x73fb80U,0x73fc30U,0x73fb98U,0x73fb88U,0x73fb8cU})if(!mw34::projection::operand(load(address_)))return 0;
 if(!mw34::projection::positive(load(0x73fb80)))return 0;
 for(unsigned i=0;i<n;++i){const unsigned at=0x7476a4+12*i;if(!mw34::projection::operand(load(at))||!mw34::projection::operand(load(at+4))||!mw34::projection::positive(load(at+8)))return 0;
  const auto&v=polygon.corners[n-1-i].vertex;unsigned u,w;std::memcpy(&u,&v.u,4);std::memcpy(&w,&v.v,4);if(load(0x72f434+32*i)!=u||load(0x72f438+32*i)!=w)return 0;}
 mw34::vkscene::HostFpEnvironment fp;
 auto instance=std::make_shared<mw34::vkscene::ModelInstance>();instance->geometry=polygon.resident;instance->world=true;const auto matrix=override_matrix(load(load(0x5eda90)));for(unsigned i=0;i<12;++i)instance->camera[i]=float(matrix[i]);
 instance->projection={world_float(0x73fb80),world_float(0x73fc30),world_float(0x73fb98),world_float(0x73fb88),world_float(0x73fb8c),world_float(0x740304)};
 if(instance->projection[5]<=0)return 0;
 const unsigned texture=load(descriptor+8)?vsurf_root(load(descriptor+8)):0;if(texture&&!vsurface(texture))return 0;
 projection_token=ProjectionToken{n,frame,scope.mesh,address,descriptor,dev->guest,texture,material,instance};++projection_candidates;
 if(projection_mode()==2){projection_dirty.prefix(n);projection_skipped+=n-1;return 1;}return 0;
}
void projection_vertices(void*destination,unsigned address,unsigned count,unsigned type,unsigned fvf,unsigned ret){
 if(!projection_token){
  if(projection_dirty.any(address,count*32)){
   std::string detail;for(unsigned i=0;i<count*32;++i)if(projection_dirty.any(address+i,1)){detail=" first_dirty="+std::to_string(address+i);break;}
   throw std::runtime_error("Unowned draw of omitted projection scratch: frame="+std::to_string(host.frames)+" ret="+std::to_string(ret)+" vertices="+std::to_string(address)+" count="+std::to_string(count)+" type="+std::to_string(type)+" fvf="+std::to_string(fvf)+detail);
  }
  get_bytes(address,destination,count*32);return;
 }
 if(ret!=0x57da68||address!=0x72f41c||count!=projection_token->count||type!=D3DPT_TRIANGLEFAN||fvf!=D3DFVF_TLVERTEX)throw std::runtime_error("GPU projection raw-copy identity mismatch");
 ++projection_host_copy;try{get_bytes(address,destination,count*32);}catch(...){--projection_host_copy;throw;}--projection_host_copy;
}
void projection_fold(const void*data,size_t count){auto*p=static_cast<const unsigned char*>(data);for(size_t i=0;i<count;++i){projection_semantic^=p[i];projection_semantic*=0x100000001b3ULL;}}
void projection_submit(D3DCmd&draw,unsigned root,unsigned ret,unsigned address,unsigned fvf,unsigned count){
 if(!projection_mode())return;
 const unsigned raw=projection_token?1:0;
 if(projection_token){const auto token=*projection_token;
  const unsigned material=load(token.frame-0x44),link=material&&readable(material,0x14)?load(material+0x10):0;
  if(material!=token.material||!link||!readable(link,8)||load(link+4)!=token.descriptor||load(token.descriptor+0xc)==4||load(0x74a268)||load(0x74a26c)!=0x3f800000||load(0x72f3c8)!=0x57d690||!projection_ftol_owned())throw std::runtime_error("GPU projection callback state changed after admission");
  if(ret!=0x57da68||root!=token.device||address!=0x72f41c||fvf!=D3DFVF_TLVERTEX||count!=token.count||draw.flags!=D3DPT_TRIANGLEFAN||!draw.indices.empty()||draw.hud_role!=WideWorld||override_suppress_draw()||frontend_on()||load(token.frame-0x34)!=token.polygon||load(token.frame-0x38)!=token.mesh||draw.texture!=token.texture||!draw.state_snapshot||draw.state_snapshot->size()<256||(*draw.state_snapshot)[D3DRENDERSTATE_ALPHABLENDENABLE]||(*draw.state_snapshot)[D3DRENDERSTATE_ALPHATESTENABLE])throw std::runtime_error("GPU projection submission contract mismatch");
  draw.model=token.instance;projection_token.reset();++projection_consumed;++world_draws;
 }
 projection_fold(&raw,4);projection_fold(&draw.flags,4);projection_fold(&count,4);projection_fold(&draw.texture,4);projection_fold(draw.state_snapshot->data(),draw.state_snapshot->size()*4);
 if(raw){const auto&model=*draw.model;projection_fold(&model.geometry->hash,8);projection_fold(model.camera.data(),12*4);projection_fold(model.projection.data(),6*4);for(unsigned i=0;i<count;++i)projection_fold(draw.vertices.data()+32*i+16,16);}
 else{projection_fold(draw.vertices.data(),draw.vertices.size());projection_fold(draw.indices.data(),draw.indices.size()*2);}
 ++projection_commands;
}
void projection_present(){
 if(!projection_mode())return;if(projection_token)throw std::runtime_error("Unconsumed GPU projection token at present");
 if(!projection_log.is_open()){const char*p=std::getenv("MW34_PROJECTION_LOG");if(!p||!*p)throw std::runtime_error("GPU projection experiment requires MW34_PROJECTION_LOG");projection_log.open(p);if(!projection_log)throw std::runtime_error("Projection log unavailable");}
 projection_log<<host.frames<<' '<<projection_commands<<' '<<projection_semantic<<' '<<projection_candidates<<' '<<projection_skipped<<' '<<projection_consumed<<' '<<projection_depth_copies<<' '<<projection_calls;for(auto r:projection_rejected)projection_log<<' '<<r;projection_log<<'\n';projection_log.flush();projection_semantic=0xcbf29ce484222325ULL;projection_commands=0;
}
