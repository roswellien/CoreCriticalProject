"""Literal persistent tree source with causal owners/imports/FS/Lockit ledgers.

Only BEFORE memory and finite allocator/API witnesses enter the machine. Tree
effects remain individual original instructions. This module does not execute
APIs, inspect candidate guards, or accept a captured AFTER machine.
"""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('accepted124_tree_parent',ROOT/'tools/m4-lockit-source/game_model.py')
G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
I=G.I;SF=G.SF;begin_root=G.begin_root;complete_root=G.complete_root
TREE_ROOT=0x4b7f70
REC=ROOT/'reports/m4-tree-source/recovery-r1'

def frozen(path,digest):
    raw=Path(path).read_bytes();I.need(hashlib.sha256(raw).hexdigest()==digest,'Exact frozen tree source contract');return json.loads(raw)

def contract():
    receipt=frozen(REC/'report.json','81efa236420aab06fb6ab63453c32fb3e1364dfdf8c268cd6e1cd815d81c20a4')
    return frozen(REC/'instruction-contracts.json',receipt['instructions_sha256'])

def source_program():
    program,callbacks=G.source_program()
    for row in contract()['instructions']:
        pc=row['pc'];I.need(pc not in program or program[pc]==row,'Identical retained/additive literal tree row');program[pc]=row
    data=frozen(ROOT/'reports/m4-tree-source/game-callbacks-r1/callbacks.json','c87fa650c12261710f58ee477cea39a570ed50cce1bcd34c49fb9239827fcee4')
    for pc,offsets in data['State_offsets_by_original_PC'].items():
        pc=int(pc);offsets=tuple(offsets);I.need(pc not in callbacks or callbacks[pc]==offsets,'Identical source undefined order');callbacks[pc]=offsets
    return program,callbacks

class Machine(G.Machine):
    def __init__(self,*args,tree_owner_resolver=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.tree_contract=contract();self.tree_owner_resolver=tree_owner_resolver
        self.tree_active=False;self.tree_started=False;self.tree_owners=[];self.tree_accesses=[]
        self.tree_publications=[];self.tree_import_definitions=[];self.tree_import_calls=[]
        self.tree_lockit_calls=[];self.tree_fs_frames=[];self.tree_fs_events=[];self.tree_insertions=[]
        self.tree_function_invocations=[];self.tree_field_writes=[];self.tree_LEAs=[]
        self.tree_pending_allocations={};self.tree_pending_lockits={};self.tree_open_FS=[]
        self.tree_site_ordinals={};self.tree_frame_ids={};self.tree_definitions={}
        self.tree_imports={(r['pc'],r['slot']):r for r in self.tree_contract['game_imports']}
        self.tree_scratch={r['CALL_pc']:r for r in self.tree_contract['Lockit_scratch_contracts']}
        self.tree_register_calls={r['pc']:r for r in self.tree_contract['register_import_calls']}
        self.tree_allocations={r['CALL_pc']:r for r in self.tree_contract['allocations']}
        self.tree_FS={}
        for frame in self.tree_contract['FS_frame_contracts']:
            for key,kind in (('read',0),('install',1),('restore',2)):
                self.tree_FS[frame[key]]=(kind,frame)

    @staticmethod
    def frame_key(frame):
        return tuple(frame[:4])

    def invocation(self,entry=None):
        for frame in reversed(self.call_stack):
            if entry is None or frame[0]==entry:
                key=self.frame_key(frame)
                if key in self.tree_frame_ids:return self.tree_frame_ids[key]
        return 0

    def boundary(self):
        cpu=list(self.projected_cpu());cpu[9]=self.cursor
        return dict(PC=self.cursor,CPU=cpu,State_hex=bytes(self.state).hex(),FX_hex=self.fx.hex(),
                    ESP=self.reg('esp'),frame_hex=self.bytes(self.reg('esp'),32).hex(),
                    FS0=int.from_bytes(self.bytes(self.word(I.BASE['fs']),4),'little'),
                    source_CS24_hex=self.bytes(0x78145640,24).hex(),source_access_index=len(self.accesses))

    def begin_tree(self):
        I.need(not self.tree_started,'Only one default tree initializer per persistent machine')
        I.need(self.cursor==TREE_ROOT and self.call_stack,'Genuine external tree CALL frame')
        I.need(self.bytes(0x60b314,8)==bytes(8),'Actual empty shared header/counter BEFORE; no seed')
        I.need(int.from_bytes(self.bytes(0x78145658,4),'little')==2,'Genuine initialized provider state2 input')
        self.tree_started=True;self.tree_active=True
        self.tree_BEFORE=self.boundary()
        self.tree_frame_ids[self.frame_key(self.call_stack[-1])]=0

    def owner_at(self,address,width=1):
        matches=[o for o in self.tree_owners if o['live'] and o['guest']<=address and address+width<=o['guest']+o['capacity']]
        I.need(len(matches)<=1,'Unique live actual tree backing owner')
        if not matches:return None
        owner=matches[0]
        I.need(address+width<=owner['guest']+owner['requested'],'Tree source access stays inside literal24B request')
        return owner

    def pointer_owner(self,pointer):
        matches=[o for o in self.tree_owners if o['live'] and o['guest']==pointer]
        I.need(len(matches)==1,'Exact live base pointer of a tree owner')
        return matches[0]

    def declare_tree_owner(self,pending,pointer,witness):
        """A finite authentic allocator result/initial backing, never an AFTER seed."""
        I.need(witness['guest']==pointer and witness['requested']==24 and witness['generation']>0,'Actual allocator pointer/request/generation')
        capacity=witness['capacity'];initial=witness['initial']
        I.need(24<=capacity<=1048576 and len(initial)==capacity,'Complete measured actual initial allocation backing')
        I.need(self.bytes(pointer,capacity)==bytes(initial),'Witness initial backing equals currently carried API allocation input')
        I.need(not any(o['guest']==pointer or o['generation']==witness['generation']for o in self.tree_owners),'Fresh actual owner identity/generation')
        owner=dict(pending,guest=pointer,native=witness.get('native',pointer),generation=witness['generation'],
                   requested=24,capacity=capacity,initial_hex=bytes(initial).hex(),live=True,published=False,index=len(self.tree_owners))
        self.tree_owners.append(owner)
        return owner

    def allocator_return(self,pending,pointer):
        if self.tree_owner_resolver is not None:witness=self.tree_owner_resolver(self,pending,pointer)
        else:
            I.need(hasattr(self,'responses'),'Finite original owner resolver or actual native responses required')
            actual=[a for a in self.responses.allocations if a['live']and a['guest']==pointer]
            I.need(len(actual)==1,'Unique actual finite API owner on literal MFC RET')
            actual=actual[0];capacity=actual['extent']
            witness=dict(guest=pointer,native=actual['native'],generation=actual['generation'],requested=24,
                         capacity=capacity,initial=self.bytes(pointer,capacity))
        return self.declare_tree_owner(pending,pointer,witness)

    def read(self,address,size=4,domain='source',pc=None):
        original_pc=self.word(2472)if pc is None else pc
        value=super().read(address,size,domain,pc)
        binding=self.tree_imports.get((original_pc,address))if self.tree_active and domain=='source'and size==4 else None
        if binding:
            I.need(value==binding['raw'],'Read actual canonical owning tree IAT before named projection')
            proof=dict(PC=original_pc,slot=address,raw=value,target=binding['target'],
                       register=binding['definition_register'],invocation=self.invocation(),
                       source_access_index=len(self.accesses)-1,step=self.steps)
            self.tree_import_definitions.append(proof)
            self.import_projections.append((9,original_pc,address,value,binding['target'],0,0,0))
            if proof['register']:self.tree_definitions[(proof['invocation'],proof['register'])]=proof
            return binding['target']
        return value

    def step(self):
        if self.cursor==TREE_ROOT and not self.tree_started:self.begin_tree()
        row=self.program.get(self.cursor)
        if row is None:return super().step()
        if self.tree_active and row['pc'] in self.tree_scratch:
            self.before_lockit_CALL(row)
        if row['mnemonic']!='setl':return super().step()
        # Exact SETL: signed comparison is SF xor OF, no changed flags.
        pc=self.cursor;self.steps+=1;I.need(self.steps<=1000000,'Finite source instruction budget')
        self.word(2472,pc);self.PCs.append(pc);self.emit('instruction-before',row=row)
        self.cursor=(pc+row['width'])&0xffffffff
        self.destination(row['decoded_operands'][0],self.flag('SF')^self.flag('OF'))
        for offset in self.callbacks.get(pc,()):
            self.state[offset]=0;self.undefined.append((pc,offset,0));self.emit('undefined',pc=pc,offset=offset,value=0)
        self.emit('instruction-after',row=row)

    def before_lockit_CALL(self,row):
        pc=row['pc'];spec=self.tree_scratch[pc]
        leas=[r for r in self.tree_LEAs if r['PC']in spec['source_LEA_pcs']and r['invocation']==self.invocation()]
        I.need(leas,'Reached Lockit CALL has an actual originating source LEA')
        lea=leas[-1];offset=(self.reg('ecx')-(self.reg('esp')-4))&0xffffffff
        I.need(lea['value']==self.reg('ecx')and offset in spec['ECX_minus_target_entry_ESP'],'Actual retained LEA value and target-entry scratch affine relation')
        if pc==0x4badd0:
            suffix=[r for r in self.accesses if r[0]in(0x4badc7,0x4badc9,0x4bacba,0x4bacd4,0x4bace5)][-2:]
            if lea['PC']==0x4badcc:
                I.need([r[0]for r in suffix]==[0x4badc7,0x4badc9]and all(r[3:]==(4,1)for r in suffix),'Causal committed outer-left terminal writes before source LEA/CALL')
                I.need(suffix[0][1]==self.reg('eax')and suffix[0][2]==self.reg('edi')and suffix[1][1]==self.reg('edi')+4 and suffix[1][2]==self.reg('eax'),'Exact terminal register/address/value joins')
        args=row['decoded_operands'];register=args[0]['register']if args[0]['kind']=='register'else None
        if register:
            expected=self.tree_register_calls[pc]
            definition=self.tree_definitions.get((self.invocation(),register))
            I.need(definition and definition['PC']==expected['definition_PC']and definition['slot']==expected['IAT']and self.reg(register)==definition['target'],'Exact earlier IAT definition retained in the real register across literal callees')
            self.tree_import_calls.append(dict(CALL_pc=pc,register=register,definition=definition,actual_register_value=self.reg(register),
                                               CALL_step=self.steps+1,intervening_source_PCs=self.PCs[definition['step']:],invocation=self.invocation()))
        self.tree_next_lockit=dict(CALL_pc=pc,role=spec['role'],invocation=self.invocation(),LEA=lea,
                                   ECX=self.reg('ecx'),target_entry_ESP=self.reg('esp')-4,scratch_offset=offset,
                                   before=self.boundary(),preceding_source_accesses=[list(r)for r in self.accesses[-4:]])

    def source_access(self,data,writing):
        pc=data['pc'];address=data['address'];width=data['bytes'];value=data['value']
        if pc not in self.tree_game_PCs:return
        owner=self.owner_at(address,width)
        if owner:
            offset=address-owner['guest']
            self.tree_accesses.append(dict(root=TREE_ROOT,pc=pc,write=writing,bytes=width,
                                           owner_CALL_pc=owner['CALL_pc'],owner_invocation_ordinal=owner['per_site_invocation_ordinal'],
                                           generation=owner['generation'],owner_index=owner['index'],owner_pointer=owner['guest'],
                                           offset=offset,address=address,value=value,source_access_index=len(self.accesses)-1,
                                           function_invocation=self.invocation()))
            if writing and width==4 and offset in(0,4,8):
                if value:self.pointer_owner(value)
            if writing and width==4 and offset==20:I.need(value in(0,1),'Literal tree color is0 or1')
        if writing:
            if address in(0x60b2f8,0x60b2f9,0x60b300,0x60b2fc,0x60b304,0x60b314,0x60b318):
                self.tree_field_writes.append(dict(pc=pc,address=address,width=width,value=value,source_access_index=len(self.accesses)-1))
            if pc in(0x4ba315,0x4ba347,0x4bab9c,0x4babac):
                published=self.pointer_owner(value)
                I.need(width==4 and not published['published'],'Exactly one primary publication per allocation invocation')
                if pc==0x4ba315:I.need(address==0x60b314 and published['CALL_pc']==0x4ba306,'Header primary publication')
                elif pc==0x4ba347:I.need(address==0x60b2fc and published['CALL_pc']==0x4ba33c,'Sentinel primary publication')
                else:I.need(owner and published['CALL_pc']==0x4bab32 and published['function_invocation']==self.invocation(),'Current literal node primary edge publishes its actual generation')
                published['published']=True
                self.tree_publications.append(dict(root=TREE_ROOT,pc=pc,address=address,value=value,
                                                   allocation_CALL_pc=published['CALL_pc'],allocation_invocation_ordinal=published['per_site_invocation_ordinal'],
                                                   generation=published['generation'],owner_index=published['index'],
                                                   target_owner_index=owner['index']if owner else None,target_owner_offset=address-owner['guest']if owner else None,
                                                   source_access_index=len(self.accesses)-1))

    @property
    def tree_game_PCs(self):
        if not hasattr(self,'_tree_game_PCs'):
            self._tree_game_PCs={r['pc']for r in self.tree_contract['instructions']if r['pc']<0x5abd00}
        return self._tree_game_PCs

    def fs_event(self,data,writing):
        pc=data['pc'];binding=self.tree_FS.get(pc)
        if binding is None or data['address']!=self.word(I.BASE['fs']):return
        kind,spec=binding;I.need(data['bytes']==4 and writing==(kind!=0),'Exact source FS direction/width')
        prior=int.from_bytes(self.bytes(data['address'],4),'little')
        if kind==0:
            frame=dict(index=len(self.tree_fs_frames),entry=spec['entry'],invocation=self.invocation(),handler=spec['handler'],
                       read_PC=pc,entry_ESP=self.reg('esp')+8,previous_head=prior,depth=len(self.tree_open_FS),closed=False)
            self.tree_fs_frames.append(frame);self.tree_pending_FS=frame
        elif kind==1:
            frame=self.tree_pending_FS;record=self.reg('esp');raw=self.bytes(record,12)
            I.need(frame['entry']==spec['entry']and struct.unpack('<3I',raw)==(frame['previous_head'],spec['handler'],0xffffffff),'Complete source-pushed12B FS record')
            I.need(data['value']==record and prior==frame['previous_head'],'Source installed head equals actual record')
            frame.update(record=record,install_PC=pc,installed_hex=raw.hex());self.tree_open_FS.append(frame)
        else:
            I.need(self.tree_open_FS,'Nested FS restore has a live source frame');frame=self.tree_open_FS[-1]
            I.need(frame['entry']==spec['entry']and prior==frame['record']and data['value']==frame['previous_head'],'Exact same invocation/head restore')
            raw=self.bytes(frame['record'],12);I.need(struct.unpack('<3I',raw)==(frame['previous_head'],spec['handler'],0xffffffff),'Whole FS record predecessor/handler/scope preserved')
            frame.update(restore_PC=pc,restored_hex=raw.hex(),closed=True);self.tree_open_FS.pop()
        self.tree_fs_events.append(dict(pc=pc,kind=kind,frame_index=frame['index'],ESP=self.reg('esp'),before_head=prior,
                                        after_head=data['value']if writing else prior,record_hex=frame.get('restored_hex',frame.get('installed_hex'))))

    def emit(self,event,**data):
        if self.tree_active:
            if event=='instruction-after'and data['row']['mnemonic']=='lea':
                row=data['row'];dest=row['decoded_operands'][0]
                if dest['kind']=='register'and dest['register']=='ecx':
                    self.tree_LEAs.append(dict(PC=row['pc'],value=self.reg('ecx'),ESP=self.reg('esp'),invocation=self.invocation(),step=self.steps))
            if event=='read-after'and data['domain']=='source':self.source_access(data,False)
            if event=='write-after'and data['domain']=='source':self.source_access(data,True)
            if event=='read-before'and data['domain']=='source':self.fs_event(data,False)
            if event=='write-before'and data['domain']=='source':self.fs_event(data,True)
            if event=='control'and data['op']=='call':
                pc=data['site'];frame=self.call_stack[-1]
                if data['target']in self.tree_contract['physical_dispatch_entries']:
                    index=len(self.tree_function_invocations)+1;self.tree_frame_ids[self.frame_key(frame)]=index
                    record=dict(index=index,entry=data['target'],CALL_pc=pc,frame=list(frame),entry_ECX=self.reg('ecx'))
                    self.tree_function_invocations.append(record)
                    if data['target']==0x4bab00:
                        record['arguments']=list(struct.unpack('<4I',self.bytes(self.reg('esp')+4,16)));self.tree_insertions.append(record)
                if pc in self.tree_allocations:
                    ordinal=self.tree_site_ordinals.get(pc,0);self.tree_site_ordinals[pc]=ordinal+1
                    I.need(int.from_bytes(self.bytes(frame[1]+4,4),'little')==24,'Literal source PUSH24 reaches allocator')
                    self.tree_pending_allocations[self.frame_key(frame)]=dict(root=TREE_ROOT,CALL_pc=pc,
                         per_site_invocation_ordinal=ordinal,function_invocation=self.invocation(),source_frame=list(frame),role=self.tree_allocations[pc]['role'])
                if pc in self.tree_scratch:
                    proof=self.tree_next_lockit;I.need(proof['CALL_pc']==pc and frame[1]==proof['target_entry_ESP'],'Actual Lockit source CALL pushes exact target frame')
                    proof['target']=data['target'];proof['entered']=self.boundary()
                    self.tree_pending_lockits[self.frame_key(frame)]=proof
            if event=='returned'and data['caller']:
                frame=data['caller'];key=self.frame_key(frame)
                if key in self.tree_pending_allocations:
                    self.allocator_return(self.tree_pending_allocations.pop(key),self.reg('eax'))
                if key in self.tree_pending_lockits:
                    proof=self.tree_pending_lockits.pop(key);proof['returned']=self.boundary()
                    I.need(data['frame']==proof['target_entry_ESP']and self.reg('esp')==data['frame']+4,'Source-derived Lockit RET consumes same frame')
                    I.need([self.reg(r)for r in('ebp','ebx','esi','edi')]==list(frame[4:8]),'Genuine literal provider preserves held-register nonvolatiles')
                    self.tree_lockit_calls.append(proof)
                if frame[0]==0x4bab00:
                    insertion=next(r for r in self.tree_insertions if r['index']==self.tree_frame_ids[key])
                    insertion['returned']=self.boundary();insertion['shape']=self.tree_shape()
        super().emit(event,**data)

    def tree_shape(self):
        header=int.from_bytes(self.bytes(0x60b314,4),'little');sentinel=int.from_bytes(self.bytes(0x60b2fc,4),'little')
        self.pointer_owner(header);self.pointer_owner(sentinel)
        fields=lambda pointer:struct.unpack('<6I',self.bytes(pointer,24))
        head=fields(sentinel);count=int.from_bytes(self.bytes(0x60b304,4),'little');visited=set();nodes=[]
        def walk(pointer,parent):
            if pointer==header:return 1
            I.need(pointer not in visited,'Literal tree has no cycle or duplicate edge');visited.add(pointer)
            owner=self.pointer_owner(pointer);I.need(owner['CALL_pc']==0x4bab32,'Every non-leaf tree edge reaches a genuine node')
            left,actual_parent,right,key,value,color=fields(pointer)
            I.need(actual_parent==parent and color in(0,1),'Inverse parent edge and literal color')
            before=len(nodes);black_left=walk(left,pointer);nodes.append(dict(pointer=pointer,index=owner['index'],key=key,value=value,color=color,left=left,right=right,parent=parent));black_right=walk(right,pointer)
            I.need(black_left==black_right,'Literal red-black balanced height')
            if color==0:I.need((left==header or fields(left)[5]==1)and(right==header or fields(right)[5]==1),'Red node has black children')
            return black_left+color
        if head[1]!=header:
            I.need(fields(head[1])[5]==1,'Literal final root is black');walk(head[1],sentinel)
        I.need(len(nodes)==count and [n['key']for n in nodes]==list(range(count)),'Ordered fixed source keys and exact count')
        I.need(not nodes or(head[0]==nodes[0]['pointer']and head[2]==nodes[-1]['pointer']),'Source-maintained sentinel min/max')
        return dict(header=header,sentinel=sentinel,count=count,root=head[1],minimum=head[0],maximum=head[2],nodes=nodes)

    def tree_result(self):
        I.need(self.tree_started and not self.tree_pending_allocations and not self.tree_pending_lockits and not self.tree_open_FS,'All literal owner/Lockit/FS prefixes returned')
        shape=self.tree_shape();I.need(shape['count']==5,'Five fixed source pair insertions completed')
        assignments={r['key']:r['static_pointer']for r in self.tree_contract['static_map_assignments']}
        I.need(all(n['value']==assignments[n['key']]for n in shape['nodes']),'Literal borrowed movement-name pointers assigned')
        I.need(all(o['published']for o in self.tree_owners),'Every allocation invocation has exactly one primary publication')
        owners=[dict(o,source_final_hex=self.bytes(o['guest'],o['capacity']).hex())for o in self.tree_owners]
        return dict(owners=owners,owned_accesses=self.tree_accesses,publications=self.tree_publications,
                    import_definitions=self.tree_import_definitions,register_import_calls=self.tree_import_calls,
                    Lockit_calls=self.tree_lockit_calls,FS_frames=self.tree_fs_frames,FS_events=self.tree_fs_events,
                    insertions=self.tree_insertions,function_invocations=self.tree_function_invocations,
                    static_field_writes=self.tree_field_writes,shape=shape,source_accesses=self.accesses,
                    candidate_AFTER_seed=False,initializers_admitted=0)
