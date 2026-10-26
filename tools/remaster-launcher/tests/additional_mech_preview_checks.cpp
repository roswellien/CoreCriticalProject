#include "../native-overrides/additional_mech_preview.hpp"
#include <limits>

void check(bool value){if(!value)throw std::runtime_error("Mech preview check failed");}
std::array<double,3> projected(const mw34::mechpreview::Camera& camera,std::array<double,3> point){
    std::array<double,3> transformed{};
    for(unsigned r=0;r<3;++r){transformed[r]=camera.matrix[4*r+3];for(unsigned a=0;a<3;++a)transformed[r]+=camera.matrix[4*r+a]*point[a];}
    return {camera.projection[3]+transformed[0]*camera.projection[0]*camera.projection[1]/transformed[2],
            camera.projection[4]+transformed[1]*camera.projection[0]*camera.projection[2]/transformed[2],transformed[2]};
}
int main(){
    // An asymmetric tall mech with long forearms, not a symmetric cube whose
    // silhouette could conceal the original per-frame fitting defect.
    std::array<double,3> low{-4,-6,0},high{4,8,14};
    const auto frame=mw34::mechpreview::framing(low,high);
    double focal{};
    for(double ysign:{-1.,1.})for(unsigned degrees=0;degrees<360;++degrees){
        const double angle=degrees*3.141592653589793/180.,c=std::cos(angle),s=std::sin(angle);
        std::array<double,16> original{c,s,0,20,0,0,-1,30,-s,c,0,40,0,0,0,1};
        const auto camera=mw34::mechpreview::camera(frame,original,2,700,ysign*600,1);
        if(!degrees)focal=camera.projection[1];
        check(camera.projection[1]==focal); // Exact constant scale over a full turn.
        const auto center=projected(camera,frame.center);
        check(std::abs(center[0]-317.5)<1e-10&&std::abs(center[1]-167.5)<1e-10);
        for(unsigned corner=0;corner<8;++corner){
            std::array<double,3> point{};for(unsigned i=0;i<3;++i)point[i]=(corner&(1<<i))?high[i]:low[i];
            const auto screen=projected(camera,point);
            check(screen[0]>=218&&screen[0]<=417&&screen[1]>=63&&screen[1]<=272&&screen[2]>1);
        }
        // A point higher on the chassis appears higher on screen, for either
        // source projection convention. Depth decreases with height: eye above target.
        auto above=frame.center;above[2]+=1;
        const auto screen=projected(camera,above);
        check(screen[1]<center[1]&&screen[2]<center[2]);
    }
    bool rejected{};try{mw34::mechpreview::framing({0,0,0},{0,0,0});}catch(const std::runtime_error&){rejected=true;}check(rejected);
}
