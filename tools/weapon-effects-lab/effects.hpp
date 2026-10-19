// Project-authored, isolated visual prototype. No guest memory or game RNG access.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <map>
#include <stdexcept>
#include <utility>
#include <vector>

namespace mw34::effects_lab {
struct Vec3 {
    double x{}, y{}, z{};
    Vec3 operator+(Vec3 b) const { return {x+b.x,y+b.y,z+b.z}; }
    Vec3 operator*(double s) const { return {x*s,y*s,z*s}; }
    bool operator==(const Vec3&) const = default;
};
inline bool finite(Vec3 v) { return std::isfinite(v.x)&&std::isfinite(v.y)&&std::isfinite(v.z); }
enum class Kind { ppc, gauss, fire, explosion, ppc_impact, gauss_muzzle, gauss_impact, ppc_muzzle };
enum class Layer { glow, spark, smoke, debris, hot_material };
struct Key {
    std::uint64_t source{};
    std::uint32_t generation{};
    bool operator==(const Key&) const = default;
};
// World coordinates: right-handed, Y up, metres and seconds in this lab ONLY.
// A future game adapter must prove native-axis/unit conversion. Velocity and
// end time here are supplied observations; this code performs no hit tests.
struct Event {
    std::uint64_t scene{};
    Key key;
    Kind kind{};
    double begin{}, end{};
    Vec3 position{}, velocity{};
};
struct Particle {
    Key key;
    std::uint32_t ordinal{};
    Vec3 position{}, color{}; // linear RGB; may exceed 1 for emissive draws
    double size{}, alpha{}, rotation{};
    Layer layer{};
    bool operator==(const Particle&) const = default;
};
struct LightRequest {
    Key key;
    Vec3 position{}, color{};
    double radius{}, intensity{}; // authored relative units, NOT calibrated lux
    bool operator==(const LightRequest&) const = default;
};
struct Ribbon {
    Key key;
    std::vector<Vec3> points;
    Vec3 color;
    double width{},alpha{};
    bool operator==(const Ribbon&) const = default;
};
struct Snapshot {
    std::uint64_t scene{};
    double time{};
    std::vector<Particle> particles;
    std::vector<LightRequest> lights;
    std::vector<Ribbon> ribbons;
    std::size_t omitted_particles{}, omitted_lights{};
    std::size_t omitted_ribbons{};
};
struct Limits {
    std::size_t events{128}, sources{1024}, particles{4096}, lights{8}, ribbons{128};
};
enum class Submit { accepted, duplicate_or_stale, wrong_scene, capacity };

inline std::uint64_t mix(std::uint64_t x) {
    x += 0x9e3779b97f4a7c15ULL;
    x = (x^(x>>30))*0xbf58476d1ce4e5b9ULL;
    x = (x^(x>>27))*0x94d049bb133111ebULL;
    return x^(x>>31);
}
inline double random(Key k, std::uint32_t ordinal, unsigned channel) {
    const auto bits=mix(k.source^mix(k.generation)^mix(ordinal)^mix(channel+0x10000ULL));
    return static_cast<double>(bits>>11)*0x1.0p-53;
}
inline double tail(Kind k) {
    switch(k) {
    case Kind::ppc: return .65;
    case Kind::gauss: return .22;
    case Kind::fire: return 2.0;
    case Kind::explosion: return 2.4;
    case Kind::ppc_impact: return 1.6;
    case Kind::gauss_muzzle: case Kind::ppc_muzzle: return .18;
    case Kind::gauss_impact: return 1.4;
    }
    throw std::invalid_argument("Unknown effect kind");
}
inline bool key_less(Key a, Key b) {
    return a.source<b.source || (a.source==b.source && a.generation<b.generation);
}
// Speed the entire impact envelope together, preserving its large geometry.
inline double effect_speed(Kind k) {
    return k==Kind::ppc_impact || k==Kind::gauss_impact ? 2.0 : 1.0;
}
inline double lightning_pulse(double age) {
    return std::min(1.,std::exp(-age*17)+.70*std::exp(-std::pow((age-.22)/.045,2))+
        .38*std::exp(-std::pow((age-.45)/.055,2)));
}
// Authored preview armor faces -X; 35-degree half-angle about that normal.
inline Vec3 armor_cone(double angle,double radialFraction) {
    const double spread=.70*std::sqrt(radialFraction);
    return {-1.,std::sin(angle)*spread,std::cos(angle)*spread};
}

class System {
    struct Record : Event {
        double stopped_at{-1};
        explicit Record(const Event& e) : Event(e) {}
    };
    std::uint64_t scene_;
    Limits limits_;
    std::vector<Record> events_;
    // Tombstones prevent stopped/reused sources being resurrected by draw callbacks.
    std::map<std::uint64_t,std::uint32_t> generations_;
public:
    explicit System(std::uint64_t scene, Limits limits={}) : scene_(scene), limits_(limits) {
        if(!scene || !limits.events || !limits.sources || limits.events>4096 ||
           limits.sources>65536 || limits.particles>65536 || limits.lights>256 || limits.ribbons>4096)
            throw std::invalid_argument("Invalid bounded effect limits/scene");
    }
    void reset(std::uint64_t scene) {
        if(!scene || scene==scene_) throw std::invalid_argument("Reset requires a new nonzero scene identity");
        scene_=scene; events_.clear(); generations_.clear();
    }
    Submit submit(const Event& e) {
        (void)tail(e.kind);
        if(!e.key.source || !e.key.generation || !std::isfinite(e.begin) ||
           !std::isfinite(e.end) || e.begin<0 || e.end<e.begin || e.end-e.begin>30 ||
           !finite(e.position) || !finite(e.velocity) ||
           std::max({std::abs(e.position.x),std::abs(e.position.y),std::abs(e.position.z),
                     std::abs(e.velocity.x),std::abs(e.velocity.y),std::abs(e.velocity.z)})>1e6)
            throw std::invalid_argument("Invalid effect event");
        if(e.scene!=scene_) return Submit::wrong_scene;
        auto g=generations_.find(e.key.source);
        if(g!=generations_.end() && e.key.generation<=g->second) return Submit::duplicate_or_stale;
        if(events_.size()>=limits_.events || (g==generations_.end()&&generations_.size()>=limits_.sources))
            return Submit::capacity;
        // Commit only after all validation and resource checks succeeded.
        events_.emplace_back(e);
        generations_[e.key.source]=e.key.generation;
        return Submit::accepted;
    }
    bool stop(std::uint64_t scene, Key key, double time) {
        if(!std::isfinite(time)||time<0) throw std::invalid_argument("Invalid stop time");
        if(scene!=scene_) return false;
        for(auto& e:events_) if(e.key==key) {
            if(time<e.begin) throw std::invalid_argument("Stop precedes activation");
            e.end=std::min(e.end,time);
            e.stopped_at=e.stopped_at<0?time:std::min(e.stopped_at,time);
            return true;
        }
        return false;
    }
    void retire_before(double time) {
        if(!std::isfinite(time)||time<0) throw std::invalid_argument("Invalid retirement time");
        std::erase_if(events_,[&](const Event& e){return time>=e.end+tail(e.kind)/effect_speed(e.kind);});
    }
    std::size_t active_records() const { return events_.size(); }
    Snapshot sample(double time) const {
        if(!std::isfinite(time)||time<0) throw std::invalid_argument("Invalid sample time");
        Snapshot out;
        out.scene=scene_; out.time=time;
        // Stable order under a bounded particle budget, independent of event submission order.
        std::vector<const Record*> ordered;
        for(const auto& e:events_) ordered.push_back(&e);
        std::sort(ordered.begin(),ordered.end(),[](auto a,auto b){return key_less(a->key,b->key);});
        auto add=[&](Particle p){
            if(out.particles.size()<limits_.particles) out.particles.push_back(p);
            else ++out.omitted_particles;
        };
        auto ribbon=[&](Ribbon r){
            if(out.ribbons.size()<limits_.ribbons)out.ribbons.push_back(std::move(r));
            else ++out.omitted_ribbons;
        };
        for(const auto* ep:ordered) {
            const auto& e=*ep;
            if(time<e.begin || time>=e.end+tail(e.kind)/effect_speed(e.kind)) continue;
            const double age=(time-e.begin)*effect_speed(e.kind), duration=(e.end-e.begin)*effect_speed(e.kind);
            // Burst births are simultaneous; continuous emitters use fixed time slots.
            const bool muzzle=e.kind==Kind::gauss_muzzle || e.kind==Kind::ppc_muzzle;
            const bool impact=e.kind==Kind::ppc_impact || e.kind==Kind::gauss_impact;
            const bool burst=muzzle || impact || e.kind==Kind::explosion;
            const double rate=e.kind==Kind::ppc?38.:(e.kind==Kind::gauss?45.:9.);
            const std::uint32_t count=burst?(muzzle?8U:(impact?(e.kind==Kind::ppc_impact?72U:192U):28U)):
                static_cast<std::uint32_t>(std::ceil(duration*rate));
            // Skip expired continuous births; no work proportional to entire mission age.
            const auto first=burst?0U:static_cast<std::uint32_t>(std::max(0.,std::floor((age-tail(e.kind))*rate)));
            const auto last=burst?count:std::min(count,static_cast<std::uint32_t>(std::floor(age*rate))+1);
            for(auto i=first;i<last;++i) {
                const double birth=burst?0.:static_cast<double>(i)/rate;
                const double a=age-birth;
                const double r0=random(e.key,i,0),r1=random(e.key,i,1),r2=random(e.key,i,2);
                const bool smoke=impact&&(e.kind==Kind::gauss_impact?i%3==0:i%4==0);
                const double life=tail(e.kind)*(smoke?(.7+.3*r0):(.3+.65*r0));
                if(a<0 || a>=life) continue;
                const double u=a/life, fade=(1-u)*(1-u);
                const double angle=r1*6.283185307179586;
                Vec3 position=e.position+e.velocity*birth;
                Vec3 color; double size,alpha; Layer layer;
                if(e.kind==Kind::ppc) {
                    const Vec3 spread{std::cos(angle)*(.15+r2*.6),r0-.5,std::sin(angle)*(.15+r2*.6)};
                    position=position+spread*a;
                    color={.55,.25,3.}; size=.035+.065*(1-u); alpha=fade*.5;
                    layer=i%5==0?Layer::spark:Layer::glow;
                } else if(e.kind==Kind::gauss) {
                    position=position+Vec3{0,(r1-.5)*.25,(r2-.5)*.25}*a;
                    color={.2,2.7,.35}; size=.025+.025*(1-u); alpha=fade*.4; layer=Layer::spark;
                } else if(e.kind==Kind::fire) {
                    // Sparse embers only; the flame/smoke body is the separate flow bake.
                    position=position+Vec3{std::sin(birth*3+a*4)*.25,.8+r0*1.4,std::cos(angle)*.15}*a;
                    color={2.3,1.1*(1-u)+.1,.025};size=.016+.02*r0;alpha=fade;layer=Layer::spark;
                } else if(muzzle) {
                    position=position+Vec3{r0*.7,(r1-.5)*.16,(r2-.5)*.16};
                    color=e.kind==Kind::gauss_muzzle?Vec3{.5,4.,.7}:Vec3{1.3,.8,4.};
                    size=.025+.09*(1-u);alpha=fade;layer=Layer::glow;
                } else if(impact) {
                    const bool ppc=e.kind==Kind::ppc_impact;
                    const bool ablative=!ppc&&!smoke&&i%7==0;
                    const double speed=smoke?(ppc?1.5+r2*3:4.+r2*8):(5+r2*(ppc?12:22));
                    // Outward cone about the preview surface normal (-X).
                    const Vec3 direction=ppc?Vec3{std::cos(angle),std::sin(angle),r0-.5}:
                        armor_cone(angle,r0);
                    position=position+direction*(speed*a*(ppc&&!smoke?.35:(ablative?.45:1.))/(1+a*(smoke?1.:2.5)))+
                        Vec3{0,smoke?.6:-3.5,0}*(a*a);
                    const bool hotMetal=!ppc&&i%5==0;
                    color=ppc?Vec3{.7,.35,4.}:Vec3{.36+.18*r0,.31+.16*r0,.26+.14*r0};
                    if(hotMetal)color={2.8,1.5,.5};
                    if(ablative)color={3.,1.2,.2};
                    if(smoke)color=ppc?Vec3{.18,.17,.27}:Vec3{.48,.40,.30};
                    size=smoke?(ppc?.28:.18)+(ppc?.95:1.05)*u:(ablative?.16+.45*u:(!ppc&&!hotMetal?.05+.13*r0:.035+.07*r0));
                    alpha=smoke?(ppc?.48:.7)*std::sin(u*3.141592653589793):std::pow(1-u,1.3)*(ppc?.55:1.);
                    if(ablative)alpha*=std::exp(-a*8);
                    layer=smoke?Layer::smoke:(ablative?Layer::glow:(ppc||hotMetal?Layer::spark:Layer::debris));
                } else {
                    const double y=r0*1.7-.25;
                    const double radial=std::sqrt(std::max(0.,1-y*y));
                    const double speed=smoke?(.5+r2*1.5):(1.+r2*7.);
                    position=position+Vec3{std::cos(angle)*radial,y,std::sin(angle)*radial}*(speed*a)+
                        Vec3{0,smoke?.3:-2.,0}*(a*a);
                    color={2.3,.6+1.0*(1-u),.07};layer=Layer::spark;
                    size=.018+.018*r0;alpha=fade;
                }
                add({e.key,i,position,color,size,alpha,r2*6.283185307179586,layer});
            }
            if(e.kind==Kind::ppc && age<duration) {
                add({e.key,0xffffffffU,e.position+e.velocity*age,{1.6,1.2,5.},.12,1,0,Layer::glow});
            }
            if((e.kind==Kind::ppc || e.kind==Kind::gauss) && age<duration){
                const bool ppc=e.kind==Kind::ppc;
                const double speed=std::sqrt(e.velocity.x*e.velocity.x+e.velocity.y*e.velocity.y+e.velocity.z*e.velocity.z);
                const double span=std::min(age,(ppc?3.3:2.1)/std::max(.001,speed));
                // Coherent continuous strands; all vertices share the same source time.
                for(unsigned strand=0;strand<(ppc?3U:1U);++strand){
                    Ribbon r{e.key,{},ppc?Vec3{.38,.18,2.6}:Vec3{.2,2.8,.3},ppc?.055:.035,ppc?.72:.9};
                    for(unsigned j=0;j<=32;++j){const double q=static_cast<double>(j)/32.;
                        const double bt=age-span*(1-q),phase=bt*42+strand*2.3;
                        const double bend=(ppc?.10:.025)*std::sin(q*3.141592653589793);
                        auto p=e.position+e.velocity*bt;
                        p.y+=bend*(std::sin(phase)+.45*std::sin(phase*2.7));
                        p.z+=bend*std::cos(phase*1.6);r.points.push_back(p);}
                    ribbon(std::move(r));
                }
            }
            if(impact && age<tail(e.kind)){
                const bool ppc=e.kind==Kind::ppc_impact;
                if(ppc && age<.76){
                    // Every primary discharge starts at the hit and explodes OUTWARD.
                    // Forks split from those channels; no incoming/sky lightning bolt.
                    const auto epoch=static_cast<unsigned>(age*12);
                    const double pulse=.16+lightning_pulse(age)*.84;
                    for(unsigned branch=0;branch<12;++branch){
                        const double theta=(branch+(random(e.key,branch,90)-.5)*.55)*6.283185307179586/12;
                        const Vec3 direction{std::cos(theta),std::sin(theta),
                            (random(e.key,branch,91)-.5)*1.1};
                        const Vec3 tangent{-std::sin(theta),std::cos(theta),.2};
                        const double reach=.12+(2.9+random(e.key,branch,92)*1.5)*(1-std::exp(-age*26));
                        Ribbon trunk{e.key,{},Vec3{1.2,.65,4.5},.045+.025*random(e.key,branch,93),pulse*(1-age/.76)};
                        for(unsigned j=0;j<=16;++j){const double q=static_cast<double>(j)/16;
                            const double jag=(random(e.key,j+branch*17,100+epoch)-.5)*.65*std::sin(q*3.141592653589793);
                            trunk.points.push_back(e.position+direction*(reach*q)+tangent*jag);}
                        const Vec3 from=trunk.points[7];
                        ribbon(std::move(trunk));
                        const Vec3 delta=direction*(reach*.48)+tangent*((branch%2?1.:-1.)*(.7+random(e.key,branch,130)));
                        Ribbon fork{e.key,{},Vec3{.65,.3,3.5},.025,pulse*(1-age/.76)*.75};
                        for(unsigned j=0;j<=8;++j){const double q=static_cast<double>(j)/8;
                            const double jag=(random(e.key,j+branch*9,140+epoch)-.5)*.4*std::sin(q*3.141592653589793);
                            fork.points.push_back(from+delta*q+tangent*jag);}
                        ribbon(std::move(fork));
                    }
                }
                // Gauss is a kinetic contact flash, with no energy halo or shock ring.
                if(!ppc){
                    // Extra hot shower: fast fine sparks plus slower lingering ember motes.
                    // Lifetime stays inside the existing impact envelope; no extra lights.
                    for(unsigned mote=0;mote<160;++mote){
                        const bool ember=mote%4==0;
                        const double r0=random(e.key,mote,210),r1=random(e.key,mote,211),r2=random(e.key,mote,212);
                        const double life=ember?.95+.40*r0:.55+.65*r0;
                        if(age>=life)continue;
                        const double u=age/life,theta=r1*6.283185307179586;
                        const double speed=ember?4.+r2*7:14.+r2*22;
                        const Vec3 velocity=armor_cone(theta,.25+.75*r0)*speed;
                        const Vec3 p=e.position+velocity*(age/(1+age*(ember?1.:2.)))+
                            Vec3{0,-(ember?1.6:3.)*age*age,0};
                        const double cooling=std::pow(1-u,.8);
                        add({e.key,0xfffe0000U+mote,p,{(ember?3.:5.)*cooling,(ember?1.1:2.5)*cooling,.10*cooling},
                            (ember?.028:.018)+r2*(ember?.035:.025),cooling,
                            theta+age*(ember?2.:5.),ember?Layer::glow:Layer::spark});
                    }
                    // Three axial stations widen away from the apex at the hit.
                    if(age<.62)for(unsigned lobe=0;lobe<9;++lobe){
                        const double station=static_cast<double>(lobe/3+1)/3;
                        const double theta=static_cast<double>(lobe%3)*6.283185307179586/3+station*1.1;
                        const double growth=1-std::exp(-age*22);
                        const double spread=(.04+.46*station)*growth;
                        const Vec3 offset{-1.6*station*growth,std::sin(theta)*spread,std::cos(theta)*spread};
                        const double size=.04+(.13+.47*station)*growth;
                        add({e.key,0xffff0000U+lobe,e.position+offset*.75,{4.,1.8,.18},size*.75,
                            .95*std::pow(1-age/.62,.6),theta+age*2,Layer::hot_material});
                    }
                    if(age<.9)for(unsigned chunk=0;chunk<16;++chunk){
                        const double theta=random(e.key,chunk,190)*6.283185307179586;
                        const Vec3 delta=armor_cone(theta,random(e.key,chunk,193))*(1.2+random(e.key,chunk,191)*3);
                        add({e.key,0xffff1000U+chunk,e.position+delta*(age/(1+age))+Vec3{0,-2.5*age*age,0},
                            {3.5,1.2,.1},.055+.06*random(e.key,chunk,192),std::pow(1-age/.9,.75),
                            theta+age*8,Layer::hot_material});
                    }
                }
                const double flash=ppc?lightning_pulse(age):std::exp(-age*35),envelope=std::exp(-age*5);
                if(flash>.005)add({e.key,0xfffffffeU,e.position,{5.,5.,5.},(ppc?.10:.08)+flash*(ppc?.65:.3),flash,0,Layer::glow});
                if(ppc&&envelope>.01)add({e.key,0xfffffffdU,e.position,Vec3{.6,.2,4.},.2+envelope*.6,envelope*.75,0,Layer::glow});
            }
            if(muzzle && age<.15){
                const double f=1-age/.15;
                Ribbon flare{e.key,{e.position,e.position+Vec3{.8*f,0,0}},
                    e.kind==Kind::gauss_muzzle?Vec3{.4,3.,.5}:Vec3{.6,.35,3.},.18*f,f};
                ribbon(std::move(flare));
            }
            // Representative lights, not one light per sprite. Never emitted from draw calls.
            double intensity=0, radius=0; Vec3 color,position=e.position;
            switch(e.kind) {
            case Kind::ppc:
                if(age<duration){ intensity=2.;radius=4.;color={.4,.3,1.};position=position+e.velocity*age; }
                break;
            case Kind::gauss:
                if(age<duration){intensity=1.8;radius=3.;color={.2,.9,.2};position=position+e.velocity*age;}break;
            case Kind::fire:
                if(age<duration){
                    intensity=1.1+.2*std::sin(age*17)+.1*std::sin(age*31);
                    radius=3.8*(1+.12*std::sin(age*2.1));color={1.,.28,.035};
                    // Same broad source wobble as the offline flow, in lab-world units.
                    position.x+=(2.8*std::sin(time*2.1)+1.8*std::sin(time*4.7))*4.8/64;
                    position.y+=.55;
                }
                break;
            case Kind::explosion:
                intensity=6.*std::pow(std::max(0.,1-age/.65),2);radius=7.;color={1.,.35,.06};break;
            case Kind::ppc_impact:
                intensity=10.*lightning_pulse(age);radius=8.;color={.35,.2,1.};break;
            case Kind::gauss_impact:
                if(age<.62)intensity=8.*std::exp(-age*6);
                radius=5.;color={1.,.55,.16};break;
            case Kind::gauss_muzzle: case Kind::ppc_muzzle:
                intensity=2.5*std::max(0.,1-age/.13);radius=3.;
                color=e.kind==Kind::gauss_muzzle?Vec3{.2,.9,.2}:Vec3{.4,.3,1.};break;
            }
            if(e.stopped_at>=0 && time>=e.stopped_at) intensity=0;
            if(intensity>0) out.lights.push_back({e.key,position,color,radius,intensity});
        }
        std::sort(out.lights.begin(),out.lights.end(),[](const auto& a,const auto& b){
            if(a.intensity!=b.intensity) return a.intensity>b.intensity;
            return key_less(a.key,b.key);
        });
        if(out.lights.size()>limits_.lights) {
            out.omitted_lights=out.lights.size()-limits_.lights;
            out.lights.resize(limits_.lights);
        }
        return out;
    }
};
} // namespace mw34::effects_lab
