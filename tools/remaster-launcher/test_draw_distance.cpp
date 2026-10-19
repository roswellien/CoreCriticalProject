// Asset-free contract fixture: includes the actual authored camera/fog helper.
#define _CRT_SECURE_NO_WARNINGS
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
namespace mw34::vkscene {
struct HostFpEnvironment {};
struct Draw { struct {unsigned mode[4]{};} push; bool model{};unsigned first{},count{};};
struct Scene {std::vector<Draw> draws;std::vector<unsigned char> vertices;};
}
struct Register {unsigned dword{};};
struct State {struct {Register rcx,rsp;} gpr;};
using Body=void*(*)(State*,unsigned,void*);
struct MockStage {
 State state;
 struct {struct {unsigned width=1920,height=1080;} display;unsigned frames{};} host;
 unsigned zoom_display_owner{};
 std::map<unsigned,unsigned> memory;
 std::map<unsigned,std::string> names;
 std::vector<std::pair<unsigned,unsigned>> regions;
 bool wide{};
 unsigned marker_calls{};
 bool readable(unsigned a,unsigned n){for(auto [b,s]:regions)if(a>=b&&std::uint64_t(a)+n<=std::uint64_t(b)+s)return true;return false;}
 unsigned load(unsigned a){return memory[a];}
 void store(unsigned a,unsigned v){memory[a]=v;}
 float wide_float(unsigned a){unsigned v=load(a);float f;std::memcpy(&f,&v,4);return f;}
 void wide_store_float(unsigned a,float f){unsigned v;std::memcpy(&v,&f,4);store(a,v);}
 [[noreturn]] void deny(const std::string&s,unsigned){throw std::runtime_error(s);}
 std::string pose_name(unsigned a,unsigned){return names[a];}
 bool wide_on(){return wide;}
 void*target_marker_body(State*s,unsigned t,void*p,Body b){++marker_calls;return b(s,t,p);}
 void region(unsigned a,unsigned n){regions.push_back({a,n});}
 void camera(unsigned node,unsigned data,unsigned view,unsigned vd,const char*name,unsigned x,unsigned y,unsigned w,unsigned h){
  region(node,0x3c);region(data,0x1dc);region(view,0x3c);region(vd,16);
  store(node+0x34,1);store(node+0x38,data);names[node]=name;store(data+4,view);
  store(view+0x34,3);store(view+0x38,vd);store(vd,x);store(vd+4,y);store(vd+8,w);store(vd+12,h);
  wide_store_float(data+0xb0,1);wide_store_float(data+0xb4,800);
 }
 #include "native-overrides/draw_distance_stage.inc"
};
static void check(bool ok,const char*message){if(!ok)throw std::runtime_error(message);}
static bool close(float a,float b){return std::abs(a-b)<.0001f;}
constexpr unsigned main_node=0x10000,main_data=0x11000,zoom_node=0x14000,zoom_data=0x15000;
constexpr unsigned fields[]={0x74a240,0x74a244,0x74a248,0x74a24c,0x74a250,0x74a260};
static void setup(MockStage&s){
 s.region(0x9000,8);s.store(0x5f4c8c,0x9000);s.store(0x9004,main_node);
 s.camera(main_node,main_data,0x12000,0x13000,"worldcam",0,0,1920,1080);
 s.camera(zoom_node,zoom_data,0x16000,0x17000,"zoomcam",1400,100,400,300);
 s.region(0x20000,0x2408);s.store(0x20000,0x5c03e8);s.store(0x20034,0x25000);
 s.region(0x26508,0x3c);s.store(0x26508,0x5c0608);s.store(0x26540,zoom_node);
 s.wide_store_float(0x74a240,32);s.wide_store_float(0x74a244,1024);
 s.wide_store_float(0x74a248,750);s.wide_store_float(0x74a24c,750*750);
 s.wide_store_float(0x74a250,1.f/718);s.wide_store_float(0x74a260,.23f);
 s.store(0x74a22c,1);s.store(0x74a230,1);
 for(unsigned a=0x74a234;a<=0x74a23c;a+=4)s.store(a,0x3f012345+a);
 for(unsigned a=0x74a254;a<=0x74a25c;a+=4)s.store(a,0x42123456+a);
}
static void verify_fog(MockStage&s){
 check(close(s.wide_float(0x74a240),32.f*1100/750),"fog near");
 check(s.wide_float(0x74a248)==1100,"fog far");
 float n=s.wide_float(0x74a240);
 check(close(s.wide_float(0x74a244),n*n),"fog near square");
 check(s.wide_float(0x74a24c)==1210000,"fog far square");
 check(close(s.wide_float(0x74a250),1.f/(1100-n)),"fog reciprocal");
 check(s.distance_fog_active&&s.distance_fog_scaled,"active fog flags");
}
static void* scoped(State*,unsigned,void*p){auto&s=*static_cast<MockStage*>(p);s.distance_prepare(main_node);verify_fog(s);return p;}
static void* throwing(State*,unsigned,void*p){scoped(nullptr,0,p);throw std::runtime_error("expected");}
static void* zoom_scoped(State*,unsigned,void*p){auto&s=*static_cast<MockStage*>(p);s.distance_prepare(zoom_node);verify_fog(s);return p;}
static void* zoom_bound(State*,unsigned,void*p){auto&s=*static_cast<MockStage*>(p);check(s.load(0x9004)==main_node,"zoom fixture must retain main context");s.distance_fog_bound(zoom_data);verify_fog(s);return p;}
static void* zoom_bound_throw(State*s,unsigned t,void*p){zoom_bound(s,t,p);throw std::runtime_error("expected");}
static void* reject_zoom_bound(State*,unsigned,void*p){auto&s=*static_cast<MockStage*>(p);auto before=s.memory;s.distance_fog_bound(zoom_data);check(s.memory==before,"unauthenticated zoom bind changed fog");return p;}
// Cached renderer binding must apply fog even when no frustum hook is dispatched.
static void* bound(State*,unsigned,void*p){auto&s=*static_cast<MockStage*>(p);s.distance_fog_bound(main_data);verify_fog(s);return p;}
static void* bound_throw(State*s,unsigned t,void*p){bound(s,t,p);throw std::runtime_error("expected");}
static void* bound_nested(State*,unsigned,void*p){auto&s=*static_cast<MockStage*>(p);s.distance_fog_bound(main_data);verify_fog(s);auto saved=s.memory;
 s.distance_camera_body(&s.state,0,p,bound);check(s.memory==saved,"nested bind far-field byte restoration");verify_fog(s);
 try{s.distance_camera_body(&s.state,0,p,bound_throw);check(false,"missing nested bind throw");}catch(const std::runtime_error&e){check(std::string(e.what())=="expected","unexpected bind failure");}
 check(s.memory==saved,"nested bind throw far-field restoration");verify_fog(s);return p;
}
static void* unbound(State*,unsigned,void*p){auto&s=*static_cast<MockStage*>(p);auto saved=s.memory;s.distance_fog_bound(zoom_data);check(s.memory==saved,"mismatched camera bind changed fog");
 s.names[main_node]="labcam";s.distance_fog_bound(main_data);check(s.memory==saved,"preview bind changed fog");s.names[main_node]="worldcam";return p;}
static void* stock_bound(State*,unsigned,void*p){auto&s=*static_cast<MockStage*>(p);auto saved=s.memory;s.distance_fog_bound(main_data);check(s.memory==saved,"800/fog0 renderer bind changed fog");return p;}
static void* legacy_inner(State*,unsigned,void*p){auto&s=*static_cast<MockStage*>(p);s.distance_fog_bound(main_data);
 check(s.wide_float(main_data+0xb4)==1600,"legacy camera range");
 check(s.wide_float(0x74a240)==64&&s.wide_float(0x74a248)==1500,"legacy fog must scale exactly once");
 check(s.wide_float(0x74a244)==4096&&s.wide_float(0x74a24c)==2250000,"legacy fog squares");
 check(close(s.wide_float(0x74a250),1.f/1436)&&close(s.wide_float(0x74a260),.115f),"legacy fog reciprocal/density");
 check(s.distance_fog_active&&s.distance_fog_scaled,"legacy active flags");return p;}
static void* legacy_throw(State*s,unsigned t,void*p){legacy_inner(s,t,p);throw std::runtime_error("expected");}
static void* legacy_outer(State*,unsigned,void*p){auto&s=*static_cast<MockStage*>(p);s.distance_prepare(main_node);legacy_inner(nullptr,0,p);auto saved=s.memory;
 s.distance_camera_body(&s.state,0,p,legacy_inner);check(saved==s.memory,"legacy nested normal changed fog");
 try{s.distance_camera_body(&s.state,0,p,legacy_throw);check(false,"missing legacy throw");}catch(const std::runtime_error&e){check(std::string(e.what())=="expected","legacy nested failure");}
 check(saved==s.memory,"legacy nested throw changed fog");legacy_inner(nullptr,0,p);return p;}
static void* nested(State*,unsigned,void*p){auto&s=*static_cast<MockStage*>(p);s.distance_prepare(main_node);verify_fog(s);
 auto saved=s.memory;s.distance_camera_body(&s.state,0,p,scoped);check(s.memory==saved,"nested normal byte restoration");verify_fog(s);
 try{s.distance_camera_body(&s.state,0,p,throwing);check(false,"missing throw");}catch(const std::runtime_error&e){check(std::string(e.what())=="expected","unexpected nested failure");}
 check(s.memory==saved,"nested throw byte restoration");verify_fog(s);return p;
}
static void* marker(State*,unsigned,void*p){auto&s=*static_cast<MockStage*>(p);check(s.distance_marker_owner==0x20000,"marker scope");s.distance_prepare(zoom_node);return p;}
static void* marker_throw(State*s,unsigned t,void*p){marker(s,t,p);throw std::runtime_error("expected");}
int main(int argc,char**argv){try{
 MockStage s;setup(s);bool stock=argc>1&&std::string(argv[1])=="stock";
 if(stock){auto before=s.memory;s.distance_prepare(main_node);check(before==s.memory,"800/fog0 not a no-op");s.distance_camera_body(&s.state,0,&s,stock_bound);check(before==s.memory,"stock bind scope changed bytes");std::cout<<"stock no-op passed\n";return 0;}
 if(argc>1&&std::string(argv[1])=="legacy"){
  s.distance_prepare(main_node);check(s.wide_float(main_data+0xb4)==1600,"legacy camera distance");auto before=s.memory;
  s.distance_camera_body(&s.state,0,&s,legacy_outer);check(before==s.memory,"legacy outer byte restoration");
  check(!s.distance_fog_active&&!s.distance_fog_scaled,"legacy outer flags restoration");
  try{s.distance_camera_body(&s.state,0,&s,legacy_throw);check(false,"missing legacy outer throw");}catch(const std::runtime_error&e){check(std::string(e.what())=="expected","legacy outer failure");}
  check(before==s.memory&&!s.distance_fog_active&&!s.distance_fog_scaled,"legacy outer throw restoration");std::cout<<"legacy proportional fog scales once across nested scopes\n";return 0;
 }
 auto initial=s.memory;s.distance_fog_bound(main_data);check(initial==s.memory,"bind outside active scope changed fog");
 s.distance_camera_body(&s.state,0,&s,unbound);check(initial==s.memory,"unauthenticated bind scope changed bytes");
 s.distance_camera_body(&s.state,0,&s,bound_nested);check(initial==s.memory,"cached bind outer far-field restoration");
 check(!s.distance_fog_active&&!s.distance_fog_scaled,"cached bind outer flags restoration");
 s.distance_prepare(main_node);check(s.wide_float(main_data+0xb4)==1200,"main distance");check(s.load(main_data+0xf8)==1,"main frustum dirty");
 auto before=s.memory;s.distance_camera_body(&s.state,0,&s,nested);
 check(before==s.memory,"outer normal restoration incl weather");check(!s.distance_fog_active&&!s.distance_fog_scaled,"outer flags restoration");
 try{s.distance_camera_body(&s.state,0,&s,throwing);check(false,"missing outer throw");}catch(const std::runtime_error&e){check(std::string(e.what())=="expected","unexpected outer failure");}
 check(before==s.memory,"outer throw restoration");check(!s.distance_fog_active&&!s.distance_fog_scaled,"throw flags restoration");
 s.store(0x9004,main_node);s.zoom_display_owner=0x26508;s.distance_prepare(zoom_node);check(s.wide_float(zoom_data+0xb4)==1200,"zoom distance with main context");
 before=s.memory;s.distance_camera_body(&s.state,0,&s,zoom_scoped);check(before==s.memory,"zoom fog restoration incl weather");
 s.distance_camera_body(&s.state,0,&s,zoom_bound);check(before==s.memory,"zoom bind restoration with main context");
 try{s.distance_camera_body(&s.state,0,&s,zoom_bound_throw);check(false,"missing zoom bind throw");}catch(const std::runtime_error&e){check(std::string(e.what())=="expected","zoom bind failure");}
 check(before==s.memory&&!s.distance_fog_active&&!s.distance_fog_scaled,"zoom bind throw restoration");
 s.distance_restore(zoom_node);s.zoom_display_owner=0;s.state.gpr.rcx.dword=0x20000;
 s.distance_marker_body(&s.state,0,&s,marker);check(s.wide_float(zoom_data+0xb4)==1200,"marker prepares zoom before draw");check(!s.distance_marker_owner,"marker restore");
 s.wide=true;try{s.distance_marker_body(&s.state,0,&s,marker_throw);}catch(const std::runtime_error&e){check(std::string(e.what())=="expected","marker failure");}
 check(!s.distance_marker_owner&&s.marker_calls==1,"wide marker throw restoration");
 // A marker scope also authenticates the renderer binding while context stays main.
 s.distance_marker_owner=0x20000;before=s.memory;s.distance_camera_body(&s.state,0,&s,zoom_bound);check(before==s.memory,"marker-authenticated zoom bind restoration");s.distance_marker_owner=0;
 s.distance_restore(zoom_node);s.distance_prepare(zoom_node);check(s.wide_float(zoom_data+0xb4)==800,"unauthenticated zoom admitted");
 for(unsigned kind=0;kind<3;++kind){
  s.zoom_display_owner=kind==0?0xdead:0x26508;
  if(kind==1)s.store(0x26508,0);
  if(kind==2)s.store(0x26540,main_node);
  s.distance_prepare(zoom_node);check(s.wide_float(zoom_data+0xb4)==800,"invalid zoom owner admitted");
  before=s.memory;s.distance_camera_body(&s.state,0,&s,reject_zoom_bound);check(before==s.memory,"invalid zoom scope restoration");
  s.store(0x26508,0x5c0608);s.store(0x26540,zoom_node);
 }s.zoom_display_owner=0;
 for(const char*name:{"labcam","camx"}){s.names[main_node]=name;s.store(0x9004,main_node);s.distance_prepare(main_node);check(s.wide_float(main_data+0xb4)==800,"preview admitted");}
 s.names[main_node]="worldcam";s.store(0x13008,1919);s.distance_prepare(main_node);check(s.wide_float(main_data+0xb4)==800,"unknown viewport admitted");
 s.store(0x13008,1920);s.zoom_display_owner=0x26508;s.store(0x9004,zoom_node);s.store(0x17000,1900);s.distance_prepare(zoom_node);check(s.wide_float(zoom_data+0xb4)==800,"out of bounds zoom admitted");
 s.store(0x9004,main_node);for(unsigned a:{0x74a22cU,0x74a230U}){s.store(a,0);before=s.memory;s.distance_fog_active=true;s.distance_prepare(main_node);check(s.wide_float(0x74a248)==750,"disabled/nonlinear weather overwritten");s.distance_fog_active=false;s.store(a,1);}
 std::cout<<"draw/fog camera scope, weather, nesting and restoration passed\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
