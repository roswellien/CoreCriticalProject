#include "../in-game-hook/identity.hpp"
#include <iterator>

using namespace mw34::hook;
static std::string contents(const std::filesystem::path& path) {
    std::ifstream file(path, std::ios::binary);
    if (!file) throw std::runtime_error("Required FOV file unavailable");
    return {std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>()};
}
static void verify_fix(const std::filesystem::path& path) {
    const auto data = contents(path);
    if (sha256(data.data(), data.size()) != "57afb226033790cafa36f6409ee036c03dc38e42b6cc1fe8d62880b03be2205d")
        throw std::runtime_error("FOV plugin identity mismatch");
}
extern "C" DWORD WINAPI mw34_selftest(void*) {
    try { verify_fix(environment(L"MW34_FOV_FILE")); return 0; } catch (...) { return 1; }
}
extern "C" DWORD WINAPI mw34_install(void*) {
    try {
        const std::filesystem::path fix(environment(L"MW34_FOV_FILE"));
        verify_fix(fix);
        std::ofstream evidence(environment(L"MW34_HOOK_LOG"), std::ios::binary);
        if (!evidence) return 2;
        if (!LoadLibraryW(fix.c_str())) {
            evidence << "FOV LoadLibraryW failed: " << GetLastError() << '\n';
            return 3;
        }
        evidence << "FOV DLL explicitly loaded into original game before entry.\n";
        evidence.flush();
        const auto log = fix.parent_path() / L"MechWarrior3FOVFix.log";
        const auto deadline = GetTickCount64() + 10000;
        while (GetTickCount64() < deadline) {
            if (std::filesystem::exists(log)) {
                const auto text = contents(log);
                if (text.find("Failed to") != std::string::npos) {
                    evidence << "Plugin reported a signature/initialization failure.\n";
                    return 4;
                }
                if (text.find("Aspect Ratio Instruction: Address") != std::string::npos &&
                    text.find("Camera HFOV Instruction: Address") != std::string::npos &&
                    text.find("Camera VFOV Instruction: Address") != std::string::npos) {
                    // Address lines precede hook creation; allow the worker to finish.
                    Sleep(250);
                    evidence << "Plugin reported all three camera signatures; visual/HUD behavior unverified.\n";
                    return 0;
                }
            }
            Sleep(50);
        }
        evidence << "Plugin did not report all three camera signatures within ten seconds.\n";
        return 5;
    } catch (...) { return 6; }
}
BOOL WINAPI DllMain(HINSTANCE, DWORD, LPVOID) { return TRUE; }
