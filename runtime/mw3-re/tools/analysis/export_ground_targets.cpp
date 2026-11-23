#include "ground_targets.hpp"
#include <cstdio>
#include <fstream>
#include <stdexcept>
#include <vector>

int main(int argc, char **argv) {
    try {
        const bool inspect = argc == 4 && std::string(argv[1]) == "--inspect";
        if ((!inspect && argc != 3) || (argc == 4 && !inspect)) {
            std::fprintf(stderr, "Usage: mw3ground_targets [--inspect] <pinned-request.json> "
                                 "<fresh-output-directory>\n");
            return 2;
        }
        const auto request = std::filesystem::u8path(argv[inspect ? 2 : 1]);
        const auto output = std::filesystem::u8path(argv[inspect ? 3 : 2]);
        constexpr std::size_t maximum = 4 * 1024 * 1024;
        std::ifstream stream(request, std::ios::binary);
        std::string input(maximum + 1, '\0');
        if (!stream)
            throw std::runtime_error("Cannot open pinned export request");
        stream.read(input.data(), std::streamsize(input.size()));
        const auto bytes = stream.gcount();
        if (stream.bad() || bytes > std::streamsize(maximum) || (!stream.eof() && stream.fail()))
            throw std::runtime_error("Export request read/size failed");
        input.resize(std::size_t(bytes));
        if (inspect) {
            const auto selected = mw3::ground_targets::read_inspection_request(input);
            const auto result = mw3::ground_targets::inspect_source(selected);
            mw3::ground_targets::write_inspection(result, output);
        } else {
            const auto selected = mw3::ground_targets::read_request(input);
            const auto result = mw3::ground_targets::export_target(selected);
            mw3::ground_targets::write_result(result, output);
        }
        std::printf("Wrote deterministic private %s metadata\n",
                    inspect ? "source inspection" : "ground target");
        return 0;
    } catch (const std::exception &error) {
        std::fprintf(stderr, "mw3ground_targets: %s\n", error.what());
        return 1;
    }
}
