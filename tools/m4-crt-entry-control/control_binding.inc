// Same admitted State, RuntimeFX and already source-mapped FDIV provider pages.
struct ControlBinding {
 ci::Context context;unsigned control{};
 void(*extra_before)(ci::Context&,unsigned){};
 void(*extra_access)(ci::Context&,unsigned){};
 void(*extra_event)(ci::Context&,unsigned){};
 void(*extra_after)(ci::Context&){};
 explicit ControlBinding(Runtime&r,unsigned mode):context(r,*reinterpret_cast<State*>(r.remill_state().data())),control(mode){}
};
thread_local ControlBinding*control_binding{};
void control_checkpoint(Runtime&,const char*);
void control_before(ci::Context&c,unsigned target){
 require(control_binding&& &control_binding->context==&c,"Exact control observation owner");
 if(target==ci::wrapper){control_checkpoint(c.runtime,"control-projected");if(control_binding->control==36)throw std::runtime_error("Authored control observer exception");}
 else if(target==ci::provider_entry){control_checkpoint(c.runtime,"control-provider-projected");if(control_binding->control==33)c.memory.protect({0x20001000},Permissions::read);}
 if(control_binding->extra_before)control_binding->extra_before(c,target);
}
void control_access(ci::Context&c,unsigned step){
 require(control_binding&& &control_binding->context==&c,"Exact control access owner");
 const auto&v=c.accesses[step-1];
 if(control_binding->control==34&&v.pc==0x5ac5a5&&v.write)c.memory.store<unsigned>({v.address},v.value^1);
 if(control_binding->extra_access)control_binding->extra_access(c,step);
}
void control_event(ci::Context&c,unsigned step){
 require(control_binding&& &control_binding->context==&c,"Exact control route owner");
 const auto&v=c.events[step-1];
 if(control_binding->control==35&&v.kind==5)c.memory.store<unsigned>({c.frames[0].esp},c.frames[0].return_pc^1);
 if(control_binding->extra_event)control_binding->extra_event(c,step);
}
void control_wrapper_adapter(Runtime&r){
 require(control_binding&& &control_binding->context.runtime==&r&&!ci::owner&&!mn::owner,"Exact exclusive control wrapper owner");auto&c=control_binding->context;
 control_checkpoint(r,"control-before");
 c.test_before_execute=&control_before;c.test_after_access=&control_access;c.test_after_event=&control_event;ci::owner=&c;
 try{ci::wrapper_adapter(r);require(c.complete&&!c.failed&&!c.depth&&!c.boundary_depth&&!c.active,"Complete control wrapper and provider closure");if(control_binding->extra_after)control_binding->extra_after(c);control_checkpoint(r,"control-after");ci::owner=nullptr;}
 catch(...){ci::owner=nullptr;control_checkpoint(r,"control-after");throw;}
}
void control_provider_adapter(Runtime&r){
 require(control_binding&&ci::owner==&control_binding->context&& &ci::owner->runtime==&r&&!mn::owner,"Exact nested current control owner");
 control_checkpoint(r,"control-provider-before");
 try{ci::provider_adapter(r);control_checkpoint(r,"control-provider-after");}
 catch(...){control_checkpoint(r,"control-provider-after");throw;}
}
