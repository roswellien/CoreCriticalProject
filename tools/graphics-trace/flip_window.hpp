#pragma once
// Pure boundary state: no game API calls, no claim of complete command coverage.
struct FlipWindow {
    enum class Decision { ignore, arm, finish, reject };
    unsigned owner=0, thread=0;
    bool active=false, done=false;
    Decision after(unsigned surface,unsigned tid,bool primary,bool closed,bool success) {
        if(done || !primary)return Decision::ignore;
        if(!active) {
            if(!closed || !success)return Decision::ignore;
            owner=surface;thread=tid;active=true;return Decision::arm;
        }
        done=true;active=false;
        return owner==surface && thread==tid && closed && success ? Decision::finish : Decision::reject;
    }
};
static void flipWindowFixture() {
    using D=FlipWindow::Decision;
    FlipWindow good;
    if(good.after(1,2,false,true,true)!=D::ignore || good.after(1,2,true,false,true)!=D::ignore ||
       good.after(1,2,true,true,false)!=D::ignore || good.after(1,2,true,true,true)!=D::arm ||
       good.after(1,2,true,true,true)!=D::finish || good.after(1,2,true,true,true)!=D::ignore)
        throw std::runtime_error("Flip window lifecycle fixture failed");
    for(unsigned control=0;control<4;++control) {
        FlipWindow bad;
        if(bad.after(1,2,true,true,true)!=D::arm ||
           bad.after(control==0?3:1,control==1?3:2,true,control!=2,control!=3)!=D::reject)
            throw std::runtime_error("Flip window rejection fixture failed");
    }
    line("\"event\":\"flip_window_fixture\",\"passed\":true,\"negative_controls\":4");
}
