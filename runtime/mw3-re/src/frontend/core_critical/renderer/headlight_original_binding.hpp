#pragma once

#include "headlight_catalog.hpp"

#include <string_view>

namespace mw34::headlights {

inline const StockProfile *match_original(const std::vector<StockProfile> &profiles,
                                          std::string_view member, std::string_view sha256) {
    // Wire IDs follow the launcher's STOCK order. The original hash pins the close LOD.
    static constexpr std::array<std::string_view, 19> members{
        "mech_annihilator.flt", "mech_avatar.flt", "mech_blackhawk.flt",
        "mech_bushwacker.flt", "mech_cauldron.flt", "mech_champion.flt",
        "mech_daishi.flt", "mech_elemental.flt", "mech_firefly.flt",
        "mech_madcat.flt", "mech_orion.flt", "mech_owens.flt",
        "mech_puma.flt", "mech_shadowcat.flt", "mech_strider.flt",
        "mech_sunder.flt", "mech_supernova.flt", "mech_thor.flt", "mech_vulture.flt",
    };
    if (sha256.size() != 64)
        return nullptr;
    for (const auto &profile : profiles)
        if (!profile.replacement && profile.stock_id < members.size() && profile.stock_id != 7 &&
            member == members[profile.stock_id] && sha256 == profile.original_hash)
            return &profile;
    return nullptr;
}

} // namespace mw34::headlights
