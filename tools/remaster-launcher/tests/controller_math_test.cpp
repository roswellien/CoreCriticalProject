#include "../native-overrides/controller_math.hpp"
#include <sstream>
#include <iostream>
#include <fstream>

using namespace mw34::controller;
void require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
template<class F>void reject(F action){try{action();}catch(const std::runtime_error&){return;}throw std::runtime_error("Malformed controller config accepted");}
int main(int argc,char** argv){
    Axis axis;axis.validate(false);
    require(axis.adjust(-32768,false)==-1&&axis.adjust(32767,false)==1,"Stick endpoints");
    require(axis.adjust(3000,false)==0,"Deadzone");axis.inverted=true;require(axis.adjust(32767,false)==-1,"Inversion");
    Config config;config.buttons[0]=12;config.buttons[1]=12;config.triggers[1]=61;
    config.calibration[4].minimum=0;config.calibration[5].minimum=0;
    State state;Sample sample;sample.connected=true;sample.focused=true;
    sample.buttons[0]=true;state.update(config,sample);require(!state.armed&&!state.actions[12],"Held input on connection must not arm");
    sample.buttons[0]=false;state.update(config,sample);require(state.armed,"Neutral must arm");
    sample.buttons[0]=true;sample.axes[1]=-16000;sample.axes[5]=32767;state.update(config,sample);
    require(state.actions[12]==1&&state.pressed[12]&&state.actions[61]==1&&state.analog[0]>.4,"Press and analog path");
    state.update(config,sample);require(state.actions[12]==2&&!state.pressed[12],"Hold must not retrigger callback");
    sample.buttons[1]=true;sample.buttons[0]=false;state.update(config,sample);require(state.actions[12]==2,"Shared action stays held until all bindings release");
    sample.focused=false;state.update(config,sample);require(state.actions[12]==4&&state.actions[61]==4&&state.analog[0]==0&&!state.armed,"Focus loss must release and neutralize");
    sample.focused=true;state.update(config,sample);require(!state.armed&&!state.actions[61],"Held reconnect must not rearm");
    sample.buttons.fill(false);sample.axes.fill(0);state.update(config,sample);require(state.armed,"Neutral rearm");
    sample.axes[1]=-32768;sample.axes[5]=32767;state.update(config,sample);sample.connected=false;state.update(config,sample);
    require(!state.armed&&state.analog[0]==0&&state.actions[61]==4,"Unplug must stop throttle and fire");
    sample.connected=true;sample.axes.fill(0);state.update(config,sample);config.buttons[2]=27;
    sample.axes[1]=-32768;sample.buttons[2]=true;state.update(config,sample);require(state.analog[0]==0,"Stop command must override a held throttle stick");
    sample.buttons[2]=false;state.update(config,sample);require(state.analog[0]==0,"Stop must wait for throttle release");
    sample.axes[1]=0;state.update(config,sample);sample.axes[1]=-32768;state.update(config,sample);require(state.analog[0]==1,"Neutral must release throttle stop latch");
    std::ostringstream stream;stream<<"CC_MW3_CONTROLLER_V1\n"<<std::string(64,'A')<<'\n';
    for(int i=0;i<6;++i)stream<<(i>=4?0:-32768)<<" 0 32767 0.12 1 0\n";
    for(int i=0;i<26;++i)stream<<"0 ";stream<<"\n20 61\n1 0 2 3\n-1 1 1 1\n0.25\n";
    std::istringstream input(stream.str());auto parsed=Config::read(input);require(parsed.triggers[1]==61&&parsed.axes[0]==1,"Launcher wire contract");
    reject([&]{std::istringstream bad(stream.str()+"extra");Config::read(bad);});
    reject([&]{std::istringstream bad("CC_MW3_CONTROLLER_V2");Config::read(bad);});
    if(argc==2){std::ifstream exported(argv[1]);auto live=Config::read(exported);require(live.triggers[1]==61&&live.scale[0]==-1,"Actual launcher export mismatch");}
    std::cout<<"Native controller normalization, safety transitions, shared bindings and wire format passed.\n";
}
