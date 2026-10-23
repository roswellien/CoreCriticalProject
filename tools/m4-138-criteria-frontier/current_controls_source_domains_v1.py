"""Pure exact current8 Context inversion/fault recipe checks."""
import re
def prove(positive,current,controls):
 route='if(c->control_route_override)W::Component::entry_40e250(r);else b.callback(r);'
 assert current.count(route)==1
 reduced=current.replace(route,'b.callback(r);')
 additions=[line for line in reduced.splitlines(True)if line.startswith((' unsigned control_route_override{};',' void control_snapshot('))]
 assert len(additions)==2
 snapshot=next(line for line in additions if line.startswith(' void control_snapshot('))
 for token in ['widget_component_&&registry_->live_handle()','widget_component_->checkpoint(stem);widget_whole_checkpoint(r_,stem);','const auto f=first_;','r_.poisoned()','for(const auto&c:r_.calls())','widget_dump(std::string(stem)+"/routes.bin",routes.data(),routes.size()*sizeof(routes[0]));']:assert token in snapshot
 assert all(t not in snapshot for t in ['store<','protect(','seed(','r_.cpu()='])
 for line in additions:assert reduced.count(line)==1;reduced=reduced.replace(line,'')
 assert reduced==positive
 assert re.findall(r'if\(mode==(\d+)\)',controls)==[str(i)for i in range(1,9)]
 for token in ['if(phase!=135)return','c.completed==135','mode>=1&&mode<=8','cause.injected&&!task.completed&&task.error.empty()','context.runtime().poisoned()','context.completed==135&&records.size()==135','first==context.failure_reason()','p->context->cleanup_widgets();p->context->registry().finish();','cleanup.completed&&cleanup.error.empty()&&!context.registry().live_handle()','address=0x5bb52c','address=0x5a3ff0','address=0x736130','address=region=0x20001000','address=region=r.fs_base().value','c.control_route_override=1','s.addr.ds_base.dword=after','s.aflag.df=1','context.control_snapshot("same-context-before")','context.control_snapshot("same-context-after")','retry-before/Registry/','retry-after/Registry/','cleaned/Registry/']:
  assert token in controls,token
 assert controls.count('context_controls_hardware_call(&')==3
 assert 'execute('not in controls and 'seed('not in controls
 return dict(whole_positive_Context_inverse=1,current_postresource_authored_faults=8,current_fault_phase=135,complete_prefix_roots=135,current_invoke_retry_cleanup_hardware_calls=3)
