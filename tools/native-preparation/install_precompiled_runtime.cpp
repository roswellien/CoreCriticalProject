// The signed .mw3update launcher protocol verifies originals and the complete
// package before this tool runs, then validates runtime.json before activation.
// This preparer copies an already compiled runtime; it never generates code.
#define NOMINMAX
#include <windows.h>
#include <filesystem>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>

namespace fs = std::filesystem;

bool inside(const fs::path& parent, const fs::path& child) {
    auto p = parent.begin(), c = child.begin();
    for (; p != parent.end(); ++p, ++c)
        if (c == child.end() || _wcsicmp(p->c_str(), c->c_str())) return false;
    return true;
}

void no_links(const fs::path& path) {
    fs::path prefix;
    for (const auto& part : fs::absolute(path)) {
        prefix /= part;
        const DWORD attributes = GetFileAttributesW(prefix.c_str());
        if (attributes != INVALID_FILE_ATTRIBUTES && (attributes & FILE_ATTRIBUTE_REPARSE_POINT))
            throw std::runtime_error("Linked update paths are unsupported");
    }
}

int wmain(int argc, wchar_t** argv) {
    try {
        std::map<std::wstring, fs::path> arguments;
        for (int i = 1; i < argc; i += 2) {
            const std::wstring key = argv[i];
            if (i + 1 == argc || (key != L"--game" && key != L"--output" &&
                key != L"--version" && key != L"--previous") ||
                !arguments.emplace(key, argv[i + 1]).second)
                throw std::runtime_error("Invalid precompiled update arguments");
        }
        for (const auto* key : {L"--game", L"--output", L"--version"})
            if (!arguments.count(key) || arguments.at(key).empty())
                throw std::runtime_error("Missing precompiled update argument");
        wchar_t executable[32768];
        const DWORD length = GetModuleFileNameW(nullptr, executable, 32768);
        if (!length || length >= 32768) throw std::runtime_error("Update tool path unavailable");
        const auto packaged = fs::path(executable).parent_path() / L"Runtime";
        no_links(packaged); no_links(arguments.at(L"--output"));
        const auto source = fs::canonical(packaged);
        const auto output = fs::weakly_canonical(fs::absolute(arguments.at(L"--output")));
        const auto game = fs::canonical(arguments.at(L"--game"));
        if (!fs::is_regular_file(game / L"MECH3.EXE") || !fs::is_regular_file(source / L"runtime.json"))
            throw std::runtime_error("Verified game or packaged runtime is missing");
        for (const auto& protected_path : {source, game})
            if (inside(protected_path, output) || inside(output, protected_path))
                throw std::runtime_error("Update output overlaps its inputs");
        if (arguments.count(L"--previous") && fs::exists(arguments.at(L"--previous"))) {
            const auto previous = fs::canonical(arguments.at(L"--previous"));
            if (inside(previous, output) || inside(output, previous))
                throw std::runtime_error("Update output overlaps the installed version");
        }
        no_links(source); no_links(output);
        fs::create_directories(output);
        unsigned count = 0;
        for (const auto& entry : fs::recursive_directory_iterator(source)) {
            no_links(entry.path());
            if (!entry.is_regular_file() && !entry.is_directory())
                throw std::runtime_error("Unsupported packaged runtime entry");
            const auto destination = output / entry.path().lexically_relative(source);
            no_links(destination);
            if (entry.is_directory()) fs::create_directories(destination);
            else {
                fs::create_directories(destination.parent_path());
                fs::copy_file(entry.path(), destination, fs::copy_options::overwrite_existing);
                ++count;
                if (count % 100 == 0)
                    std::cout << "Preparing precompiled update: installed " << count << " files\n" << std::flush;
            }
        }
        std::cout << "Preparing precompiled update: " << count
                  << " files installed; ready for launcher validation.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Precompiled update failed: " << error.what() << '\n';
        return 1;
    }
}
