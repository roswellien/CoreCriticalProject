// Independent compiled boundary controls. Production adapters are tested as
// callbacks; no author comparator, author context tests, or vendor code runs.
#define main authored_carry_worker_entry_unused
#include "../m4-crt-control-carry/native_main.cpp"
#undef main
#include <cstddef>

namespace peer {
unsigned assertions{}, scenarios{};
std::vector<std::uint8_t> image, provider, pack, before_stream;
void demand(bool condition, const char *message) {
    ++assertions;
    if (!condition) throw std::runtime_error(message);
}
template<class T> T load(const void *p) { T v{}; std::memcpy(&v,p,sizeof(v)); return v; }
template<class T> void save(void *p,T v) {std::memcpy(p,&v,sizeof(v));}
rt::Policy policy() {rt::Policy p;p.stack_low={0x20001000};p.stack_bytes=4096;return p;}
struct Case {
    rt::Runtime runtime;
    State &state;
    control::Context boundary;
    control::SerialOwner serial;
    unsigned sequence;
    explicit Case(unsigned s=0):runtime(rt::Runtime::from_admitted_image(std::as_bytes(std::span{image}),policy())),
      state(seed_before_only(runtime,before_stream.data()+32+s*27*92388,s)),boundary(runtime,state),serial(boundary),sequence(s) {
        mount_provider(runtime,pack);register_all(runtime);++scenarios;
    }
    std::string attempt(unsigned entry,unsigned ret,carry::Native *record=nullptr) {
        carry::observation=record;
        control::HostScope host;
        std::string error;
        try {runtime.call_direct({entry},{ret});} catch(const rt::Fault &fault) {error=fault.what();}
        carry::observation=nullptr;host.capture();
        demand(!std::memcmp(host.before.bytes,host.after.bytes,416),"Host architectural FX fields restored on actual callback boundary");
        demand(!std::memcmp(host.env,host.env_after,28),"Host complete legacy ENV restored on actual callback boundary");
        return error;
    }
    void control_phase() {
        demand(attempt(control::wrapper,control::outer_return).empty(),"Actual compiled control wrapper succeeds");
        demand(!runtime.poisoned()&&runtime.calls().size()==2&&runtime.calls()[0].completed&&runtime.calls()[1].completed,
               "Actual wrapper and named service close two Runtime routes");
        demand(boundary.count==13&&!boundary.depth&&!boundary.boundary_depth&&!boundary.failed,"Actual nested provider frames close");
    }
    GuestAddress region(unsigned address) const {
        for(const auto &r:runtime.image_metadata().mapped_regions)
            if(address>=r.start.value&&std::uint64_t{address}<std::uint64_t{r.start.value}+r.size)return r.start;
        return {address&~4095U}; // two explicitly mounted provider pages
    }
    void mutated_byte(unsigned address) {
        auto page=region(address);runtime.memory().protect(page,Permissions::read|Permissions::write);
        auto byte=runtime.memory().load<std::uint8_t>({address});runtime.memory().store<std::uint8_t>({address},byte^1U);
        runtime.memory().protect(page,Permissions::read|Permissions::execute);
    }
    void numerical_denial(unsigned entry,const char *diagnosis=nullptr) {
        std::array<std::byte,512> oldfx{};std::memcpy(oldfx.data(),runtime.fx().data(),512);
        const auto mask=load<unsigned>(reinterpret_cast<std::byte *>(&state.x87)+28);
        const auto calls=runtime.calls().size();carry::Native observation{};
        auto error=attempt(entry,carry::broker,&observation);
        demand(!error.empty(),"Changed numerical precondition is rejected by the actual callback");
        if(diagnosis)demand(error.find(diagnosis)!=std::string::npos,"Intended independent mutation produces the intended diagnosis");
        demand(runtime.poisoned()&&runtime.calls().size()==calls+1&&!runtime.calls().back().completed,
               "Entered callback denial remains an incomplete poisoned real route");
        demand(!std::memcmp(oldfx.data(),runtime.fx().data(),512)&&mask==load<unsigned>(reinterpret_cast<std::byte *>(&state.x87)+28),
               "Failure cannot normalize either resident capability or Runtime FX");
        auto count=runtime.calls().size();carry::Native retry{};
        demand(!attempt(entry,carry::broker,&retry).empty()&&runtime.calls().size()==count&&!retry.state_seeded,
               "Poisoned Runtime refuses a second execution and produces no passing observation");
    }
};
void positive(unsigned sequence) {
    Case c(sequence);c.control_phase();
    const auto incoming=load<std::uint16_t>(before_stream.data()+32+sequence*27*92388+116);
    const auto expected_cw=static_cast<std::uint16_t>((incoming&~0x300U)|0x200U);
    demand(c.state.x87.fxsave.cwd.flat==expected_cw&&load<std::uint16_t>(c.runtime.fx().data())==expected_cw,
           "Measured actual control result retains rounding and selects PC53");
    // Authored opaque-state sentinel discriminates carry from repeated seeding.
    auto *opaque=reinterpret_cast<std::uint8_t *>(&c.state)+3280;
    for(unsigned i=0;i<224;++i)opaque[i]^=static_cast<std::uint8_t>(0x39+i*11);
    std::array<std::uint8_t,224> hidden{};std::memcpy(hidden.data(),opaque,224);
    // Non-numerical adapters must preserve actual legacy metadata even when
    // Runtime FX carries separately observed zero pointer/opcode metadata.
    std::array<std::byte,18> legacy{};std::memcpy(legacy.data(),reinterpret_cast<std::byte *>(&c.state.x87)+6,18);
    std::array<std::byte,18> fxmeta{};std::memcpy(fxmeta.data(),c.runtime.fx().data()+6,18);
    for(unsigned entry:carry::entries) {
        carry::Native record{};
        demand(c.attempt(entry,carry::broker,&record).empty(),"Actual selected compiled initializer succeeds with live carried state");
        demand(record.state_seeded&&record.common.host_restored&&!record.domain_error,"Actual observation is complete and admitted");
        demand(!std::memcmp(record.state_after.data(),&c.state,3504),"Recorded State is the same persistent Runtime State object");
        demand(!std::memcmp(hidden.data(),reinterpret_cast<std::uint8_t *>(&c.state)+3280,224),"Opaque State sentinel survives every callback; no reseeding");
        demand(load<unsigned>(c.runtime.fx().data()+28)==0x2ffff&&load<unsigned>(reinterpret_cast<std::byte *>(&c.state.x87)+28)==0x2ffff,
               "Temporary Request mask zero never reaches resident State or FX");
        demand(load<std::uint16_t>(c.runtime.fx().data())==expected_cw&&c.state.x87.fxsave.cwd.flat==expected_cw,
               "Actual CW carries through every selected body");
        demand(!std::memcmp(fxmeta.data(),c.runtime.fx().data()+6,18),"Separate Runtime FX metadata is carried unchanged");
        if(entry==0x410910||entry==0x410940)
            demand(!std::memcmp(legacy.data(),reinterpret_cast<std::byte *>(&c.state.x87)+6,18),"Integer chain preserves independent legacy ENV metadata");
        std::memcpy(legacy.data(),reinterpret_cast<std::byte *>(&c.state.x87)+6,18);
    }
    demand(c.runtime.calls().size()==28&&c.boundary.count==13&&!c.runtime.poisoned(),"Exact selected27 phase extent, one service, persistent owner");
}
void run() {
    positive(0);positive(11);
    for(unsigned entry:{0x410910U,0x43aec0U})for(unsigned location=0;location<3;++location)
        for(unsigned value:{0U,0x1ffffU,0x2fffeU,0xffffffffU}) {
            Case c;c.control_phase();
            if(location!=1)save<unsigned>(c.runtime.fx().data()+28,value);
            if(location!=0)save<unsigned>(reinterpret_cast<std::byte *>(&c.state.x87)+28,value);
            c.numerical_denial(entry,"Observed carry FX capability mask changed");
        }
    for(unsigned entry:{0x410910U,0x43aec0U,0x4133c0U}) {
        Case c;c.control_phase();c.runtime.memory().protect(c.region(0x604000),Permissions::read);
        c.numerical_denial(entry);
    }
    for(unsigned entry:{0x410910U,0x43aec0U,0x4133c0U}) {
        Case c;c.control_phase();c.mutated_byte(entry);c.numerical_denial(entry);
    }
    for(unsigned entry:{0x410910U,0x43aec0U,0x4133c0U}) {
        Case c;c.control_phase();c.state.addr.fs_base.dword+=4;c.numerical_denial(entry);
    }
    for(unsigned entry:{0x410910U,0x43aec0U,0x4133c0U}) {
        Case c;c.control_phase();save<unsigned>(c.runtime.fx().data()+24,0x1f81U);c.state.x87.fxsave.mxcsr.flat=0x1f81;
        c.numerical_denial(entry);
    }
    // Actual compiled source/provider refusal, not a mock adapter invocation.
    for(unsigned address:{0x780042e1U,0x7801129bU,0x5ac5a0U,0x5ac5d6U}) {
        Case c;c.mutated_byte(address);
        const auto error=c.attempt(control::wrapper,control::outer_return);
        demand(!error.empty()&&c.runtime.poisoned()&&!c.runtime.calls().front().completed,
               "Changed provider/wrapper/thunk source denies actual compiled control route");
        demand(c.boundary.failed&&c.boundary.reason,"Control boundary retains first typed source failure");
        const auto reason=c.boundary.reason;const auto pc=c.boundary.fault_pc;auto count=c.runtime.calls().size();
        demand(!c.attempt(control::wrapper,control::outer_return).empty()&&count==c.runtime.calls().size()&&reason==c.boundary.reason&&pc==c.boundary.fault_pc,
               "Retry preserves first source fault and cannot run poisoned owner");
    }
    std::cout<<"{\"passed\":true,\"checks\":"<<assertions<<",\"scenarios\":"<<scenarios
             <<",\"original_or_provider_execution\":false,\"full_startup_credit\":false}\n";
}
}
int main(int argc,char **argv) {try {
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    peer::demand(argc==5,"Exact independently bound source inputs required");
    peer::image=read(argv[1],2384384);peer::provider=read(argv[2],266293);peer::pack=read(argv[3],106716);peer::before_stream=read(argv[4],60000000);
    peer::demand(digest(peer::image)==m4::admitted_image_hash&&digest(peer::provider)==original::provider_sha&&digest(peer::pack)==original::pack_sha&&digest(peer::before_stream)==carry::original_raw_sha,
                 "Independent causal inputs match exact immutable image/provider/pack/before stream");
    peer::run();return 0;
} catch(const std::exception &error) {std::cerr<<error.what()<<'\n';return 1;}}
