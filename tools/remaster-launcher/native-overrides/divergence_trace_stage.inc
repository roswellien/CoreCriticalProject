// Opt-in, bounded source-data capture for the recurring frame-487 divergence.
// No guest memory is modified. Keep payloads private: they contain game data.
void divergence_heap(unsigned operation,unsigned address,unsigned size,unsigned zero){
 if(host.frames>280)return;
 static std::ofstream file;static bool checked{};
 if(!checked){checked=true;const char*p=std::getenv("MW34_ALLOCATION_TRACE");if(!p||!*p)return;file.open(p,std::ios::binary);if(!file)throw std::runtime_error("Allocation trace unavailable");file.write("ALC1",4);}
 if(!file.is_open())return;
 unsigned record[23]={host.frames,operation,address,size,zero,state.gpr.rsp.dword,state.gpr.rbp.dword};
 unsigned frame=state.gpr.rbp.dword;
 for(unsigned i=0;i<8&&frame&&readable(frame,8);++i){record[7+i*2]=frame;record[8+i*2]=load(frame+4);const unsigned next=load(frame);if(next<=frame)break;frame=next;}
 file.write(reinterpret_cast<const char*>(record),sizeof(record));if(!file)throw std::runtime_error("Allocation trace write failed");
}
void divergence_trace(const D3DCmd& draw){
 const unsigned frame=host.frames+1;
 if(frame<486||frame>493)return;
 static std::ofstream file;
 static bool checked{};
 if(!checked){checked=true;const char*p=std::getenv("MW34_DIVERGENCE_TRACE");if(!p||!*p)return;file.open(p,std::ios::binary);if(!file)throw std::runtime_error("Divergence trace unavailable");file.write("DVG1",4);}
 if(!file.is_open())return;
 const unsigned context=load(0x5f4c8c);
 const unsigned node=context&&readable(context,8)?load(context+4):0;
 const unsigned data=node&&readable(node,0x3c)?load(node+0x38):0;
 const unsigned stack=load(0x5eda90);
 const unsigned matrix=stack&&readable(stack,4)?load(stack):0;
 const unsigned header[]={frame,host.draw_calls,draw.flags,unsigned(draw.vertices.size()),unsigned(draw.indices.size()*2),draw.texture,node,data,matrix};
 file.write(reinterpret_cast<const char*>(header),sizeof(header));
 auto bytes=[&](unsigned address,unsigned count){std::vector<unsigned char> value(count);if(address&&readable(address,count))get_bytes(address,value.data(),count);file.write(reinterpret_cast<const char*>(value.data()),count);};
 bytes(node,0x80);bytes(data,0x1dc);bytes(matrix,48);
 for(unsigned address:{0x73fb80U,0x73fc30U,0x73fb98U,0x73fb88U,0x73fb8cU,0x740304U})bytes(address,4);
 if(!draw.state_snapshot||draw.state_snapshot->size()<256)throw std::runtime_error("Divergence trace state unavailable");
 file.write(reinterpret_cast<const char*>(draw.state_snapshot->data()),256*4);
 file.write(reinterpret_cast<const char*>(draw.vertices.data()),draw.vertices.size());
 file.write(reinterpret_cast<const char*>(draw.indices.data()),draw.indices.size()*2);
 if(!file)throw std::runtime_error("Divergence trace write failed");
}
