#include "status_model_fit.hpp"
#include <iostream>

int main() {
    try {
        unsigned checks = 0;
        auto check = [&](bool ok, const char *message) {
            ++checks;
            if (!ok)
                throw std::runtime_error(message);
        };
        for (auto box : {std::array<double, 4>{530, 370, 605, 470},
                         {10, 370, 85, 470},
                         {1060, 740, 1210, 940},
                         {20, 740, 170, 940}}) {
            for (double dx : {-70., -12., 0., 14., 90.})
                for (double dy : {-80., -9., 0., 11., 100.})
                    for (double size : {.5, 1., 2.}) {
                        const double cx = (box[0] + box[2]) * .5 + dx,
                                     cy = (box[1] + box[3]) * .5 + dy;
                        const std::array<double, 4> model{cx - 30 * size, cy - 45 * size,
                                                          cx + 30 * size, cy + 45 * size};
                        const auto fit = mw34::status::fit(model, box);
                        check(fit.scale > 0 && fit.scale <= 1, "fit enlarged preview");
                        check(model[0] * fit.scale + fit.x >= box[0] + 3 - 1e-8 &&
                                  model[2] * fit.scale + fit.x <= box[2] - 3 + 1e-8,
                              "wide model or sideways gait clips horizontally");
                        check(model[1] * fit.scale + fit.y >= box[1] + 3 - 1e-8 &&
                                  model[3] * fit.scale + fit.y <= box[3] - 3 + 1e-8,
                              "tall model or footstep clips vertically");
                    }
        }
        check(!mw34::status::fit({545, 380, 590, 460}, {530, 370, 605, 470}).changed(),
              "already-fitting original framing changed");
        const auto target = mw34::status::fit({8, 350, 90, 490}, {10, 370, 85, 470});
        const auto player = mw34::status::fit({545, 380, 590, 460}, {530, 370, 605, 470});
        check(target.changed() && !player.changed(), "target and player framing coupled");
        std::cout << "PASS: " << checks << " status model fit checks\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "FAIL: " << error.what() << '\n';
        return 1;
    }
}
