#include "graphics/menu_version.hpp"
#include <cassert>
#include <cstdlib>
#include <string>
int main(int argc,char**argv) {
    _putenv_s("MW34_CORE_CRITICAL_VERSION",argc>1?argv[1]:"1.0.34");
    const std::string original="MechWarrior 3 1.2.22.0";
    if(argc>1) { assert(mw34::menu_version::caption(original)==original);return 0; }
    assert(mw34::menu_version::caption(original)=="Core Critical 1.0.34 - "+original);
    assert(mw34::menu_version::caption(L"MechWarrior 3 Remastered")==L"Core Critical 1.0.34 - MechWarrior 3 Remastered");
    assert(mw34::menu_version::caption("Core Critical 1.0.34 - MechWarrior 3 1.2.22.0")=="Core Critical 1.0.34 - MechWarrior 3 1.2.22.0");
    assert(mw34::menu_version::caption("Other window")=="Other window");
    assert(mw34::menu_version::caption("").empty());
}
