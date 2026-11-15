#include "ground_targets.hpp"
#include "frontend/core_critical/renderer/native_surface_identity.hpp"
#include "frontend/core_critical/renderer/native_texture_identity.hpp"
#include "frontend/core_critical/renderer/surface_materials.hpp"
#include "gamez/zclass/cls_zbd.h"
#include "gamez/zclass/list.h"
#include "gamez/zimage/zimg_library.h"
#include "gamez/zimage/zimg_texture.h"
#include "gamez/zmodel/gmod_const.h"
#include "gamez/zmodel/gmod_fog.h"
#include "gamez/zrender/zrndr_fog.h"
#include "gamez/zutil/zutl_path.h"
#include "gamez/zvideo/zvid_ddd3d.h"
#include "gamez/zvideo/zvid_format.h"
#include "platform/sha256.hpp"
#include <algorithm>
#include <array>
#include <cfenv>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <limits>
#include <map>
#include <memory>
#include <nlohmann-json/json.hpp>
#include <set>
#include <sstream>
#include <stdexcept>

namespace mw3::ground_targets {
namespace {
namespace fs = std::filesystem;
using Json = nlohmann::json;
constexpr std::uint64_t limit = 512ULL * 1024 * 1024;
constexpr std::uint64_t metadata_limit = 4ULL * 1024 * 1024;
[[noreturn]] void fail(const char *reason) {
    throw std::runtime_error(std::string("Ground export: ") + reason);
}
void require(bool value, const char *reason) {
    if (!value)
        fail(reason);
}
std::string lower(std::string value) {
    for (auto &c : value)
        if (c >= 'A' && c <= 'Z')
            c += 'a' - 'A';
    return value;
}
bool member_valid(const std::string &value) {
    if (value.empty() || value.size() > 1024 || value.front() == '/' || value.back() == '/' ||
        value.find_first_of("\\:\0", 0, 3) != std::string::npos || lower(value) != value)
        return false;
    std::istringstream pieces(value);
    std::string part;
    while (std::getline(pieces, part, '/'))
        if (part.empty() || part == "." || part == "..")
            return false;
    return true;
}
bool digest_valid(const std::string &value) {
    return value.size() == 64 && value.find_first_not_of("0123456789abcdef") == std::string::npos;
}
std::string hex(std::uint64_t value) {
    std::ostringstream out;
    out << std::hex << std::setfill('0') << std::setw(16) << value;
    return out.str();
}
void fields(const Json &value, std::initializer_list<const char *> names) {
    require(value.is_object() && value.size() == names.size(), "unknown/missing JSON fields");
    for (const auto name : names)
        require(value.contains(name), "missing JSON field");
}
std::string text(const Json &value) {
    require(value.is_string(), "expected string");
    auto result = value.get<std::string>();
    require(!result.empty() && result.size() <= 4096 && result.find('\0') == std::string::npos,
            "invalid string");
    return result;
}
std::uint64_t number(const Json &value) {
    require(value.is_number_integer() &&
                (!value.is_number_integer() || value.is_number_unsigned() ||
                 value.get<std::int64_t>() >= 0),
            "expected unsigned integer");
    return value.get<std::uint64_t>();
}
void validate(const Request &r) {
    require(r.data_root.is_absolute() && r.bank_root.is_absolute(),
            "input roots must be explicit absolute paths");
    require(r.region == "t1", "initial export supports unchanged Training only");
    require(member_valid(r.member) && r.region.size() <= 32 &&
                r.region.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789_") ==
                    std::string::npos &&
                r.member == "zbd/" + r.region + "/gamez.zbd",
            "source/region is not canonical");
    require(digest_valid(r.sha256) && r.bytes > 0 && r.bytes <= limit && r.model_slot < 1048576,
            "invalid source pin/selector");
    require(mw34::materials::valid_surface_identifier(
                r.asset_id, mw34::materials::max_surface_identifier_bytes, true) &&
                member_valid(r.surface_materials),
            "invalid authored asset/sidecar member");
    require(r.asset_id == r.region + "-model-" + std::to_string(r.model_slot),
            "asset ID must name its canonical region/model selector");
    require(r.textures.size() <= 4096, "too many texture selectors");
    std::set<std::string> names;
    for (const auto &t : r.textures) {
        require(!t.texture.empty() && t.texture.size() < 20 &&
                    t.texture.find('\0') == std::string::npos && !t.entry.empty() &&
                    t.entry.size() < 32 && t.entry.find('\0') == std::string::npos &&
                    lower(t.entry) == lower(t.texture) && names.insert(lower(t.texture)).second,
                "ambiguous texture selector");
        require(member_valid(t.member) && digest_valid(t.sha256) && t.bytes >= 24 &&
                    t.bytes <= std::uint64_t(std::numeric_limits<long>::max()) && t.mip == 0,
                "unsupported bank pin or mip (base mip0 only)");
    }
}
fs::path contained(const fs::path &root, const std::string &member) {
    const auto base = fs::canonical(root), file = fs::canonical(base / fs::u8path(member));
    auto left = base.begin(), right = file.begin();
    for (; left != base.end(); ++left, ++right)
        require(right != file.end() && *left == *right, "resolved input escapes pinned root");
    require(right != file.end() && fs::is_regular_file(file),
            "input is not a contained regular file");
    return file;
}
using File = std::unique_ptr<std::FILE, int (*)(std::FILE *)>;
File open_file(const fs::path &path) {
#if defined(_WIN32)
    std::FILE *f{};
    _wfopen_s(&f, path.c_str(), L"rb");
#else
    auto *f = std::fopen(path.c_str(), "rb");
#endif
    require(f != nullptr, "input open failed");
    return File(f, std::fclose);
}
std::string hash_file(std::FILE *file, std::uint64_t bytes) {
    require(std::fseek(file, 0, SEEK_SET) == 0, "input hash seek failed");
    platform::integrity::Sha256 hash;
    std::array<unsigned char, 65536> buffer;
    std::uint64_t length = 0;
    for (;;) {
        const auto n = std::fread(buffer.data(), 1, buffer.size(), file);
        if (!n) {
            require(!std::ferror(file), "input hash read failed");
            break;
        }
        require(n <= bytes - std::min(bytes, length), "input grew beyond pinned bytes");
        hash.update(buffer.data(), n);
        length += n;
    }
    require(length == bytes && std::fseek(file, 0, SEEK_SET) == 0, "input size/rewind differs");
    return hash.hex();
}
// The helper has no live host. All canonical global pools/settings are
// temporarily owned here; raw strict allocations die after these containers.
struct Isolation {
    static std::fenv_t save_fp() {
        std::fenv_t fp;
        require(std::fegetenv(&fp) == 0, "cannot preserve FP environment");
        return fp;
    }
    // Finish potentially throwing snapshots before moving any canonical pool.
    std::fenv_t fp = save_fp();
    zimg::State image = zimg::state();
    zutl::Mounts mounts = zutl::mounts();
    zcls::NodePool nodes = std::move(zcls::nodes());
    zcls::Lists lists = std::move(zcls::lists());
    zmod::ModelPool models = std::move(zmod::models());
    zmod::MaterialTable materials = std::move(zmod::materials());
    zimg::TextureTable textures = zimg::textures();
    zmod::Fog fog = zmod::fog();
    zrndr::FogColor fog_color = zrndr::fog_color();
    zrndr::DeviceFog device_fog = zrndr::device_fog();
    zvid::PixelFormat pixels = zvid::pixel_format();
    zvid::ChannelMasks masks = zvid::channel_masks();
    zvid::Display display = zvid::display();
    std::array<char, 0x30> remembered{};
    explicit Isolation(zutl::Mounts selected) {
        std::memcpy(remembered.data(), zcls::zbd_path(), remembered.size());
        zcls::nodes() = {};
        zcls::lists() = {};
        zmod::models() = {};
        zmod::materials() = {};
        zimg::textures() = {};
        zimg::state() = {};
        zimg::state().display_format = 6;
        zutl::mounts() = std::move(selected);
        zrndr::device_fog().active = 0;
        zrndr::device_fog().send = nullptr;
        zvid::set_pixel_format(5, 6, 5);
        zvid::channel_masks() = {};
        zvid::display() = {};
        zvid::display().device = false;
    }
    ~Isolation() {
        zcls::nodes() = std::move(nodes);
        zcls::lists() = std::move(lists);
        zmod::models() = std::move(models);
        zmod::materials() = std::move(materials);
        zimg::textures() = textures;
        zimg::state() = std::move(image);
        zutl::mounts() = std::move(mounts);
        zmod::fog() = fog;
        zrndr::fog_color() = fog_color;
        zrndr::device_fog() = device_fog;
        zvid::pixel_format() = pixels;
        zvid::channel_masks() = masks;
        zvid::display() = display;
        std::memcpy(zcls::zbd_path(), remembered.data(), remembered.size());
        std::fesetenv(&fp);
    }
};
struct Bank {
    fs::path path;
    std::string sha256;
    std::uint64_t bytes{};
    File file{nullptr, std::fclose};
    std::vector<zimg::Entry> entries;
    zimg::Library library{};
};
std::unique_ptr<Bank> bank_open(const Request &r, const TexturePin &pin,
                                zcls::ZbdReadContext &proof) {
    proof.allocate(sizeof(Bank) + 8192);
    auto bank = std::make_unique<Bank>();
    bank->path = contained(r.bank_root, pin.member);
    bank->sha256 = pin.sha256;
    bank->bytes = pin.bytes;
    bank->file = open_file(bank->path);
    require(hash_file(bank->file.get(), pin.bytes) == pin.sha256, "bank SHA differs");
    auto &library = bank->library;
    require(std::fread(&library.header, sizeof library.header, 1, bank->file.get()) == 1 &&
                library.header.has_entries == 1 && library.header.texture_count > 0 &&
                library.header.texture_count <= 1048576 && library.header.palette_count == 0,
            "unsupported bank header (nonpaletted only)");
    const auto table_bytes = std::uint64_t(library.header.texture_count) * sizeof(zimg::Entry);
    require(table_bytes <= pin.bytes - 24, "bank table span exceeds file");
    proof.allocate(table_bytes);
    bank->entries.resize(std::size_t(library.header.texture_count));
    require(std::fread(bank->entries.data(), std::size_t(table_bytes), 1, bank->file.get()) == 1,
            "bank table read failed");
    std::set<std::string> names;
    proof.allocate(std::uint64_t(library.header.texture_count) * 128);
    for (const auto &e : bank->entries) {
        require(std::memchr(e.name, 0, sizeof e.name) && e.name[0] &&
                    names.insert(lower(e.name)).second && e.offset >= 24 + table_bytes &&
                    std::uint64_t(e.offset) < pin.bytes && e.palette == -1,
                "ambiguous/unbounded bank entry");
    }
    require(pin.bytes <= std::uint64_t(std::numeric_limits<long>::max()),
            "bank exceeds canonical seek range");
    library.file = bank->file.get();
    library.entries = bank->entries.data();
    library.size = long(pin.bytes);
    library.needs_resolve = false;
    return bank;
}
std::pair<mw34::materials::SurfaceKey, Json> texture_key(Bank &bank, const TexturePin &pin,
                                                         zcls::ZbdReadContext &proof) {
    const auto found = std::find_if(bank.entries.begin(), bank.entries.end(),
                                    [&](const zimg::Entry &e) { return pin.entry == e.name; });
    require(found != bank.entries.end(), "exact bank texture member is missing");
    auto end = bank.bytes;
    for (const auto &e : bank.entries)
        if (e.offset > found->offset)
            end = std::min(end, std::uint64_t(e.offset));
    require(end - found->offset >= 16 &&
                std::fseek(bank.file.get(), long(found->offset), SEEK_SET) == 0,
            "texture header span/seek invalid");
    std::array<unsigned char, 16> info{};
    require(std::fread(info.data(), info.size(), 1, bank.file.get()) == 1,
            "texture info read failed");
    std::uint32_t flags;
    std::int16_t width, height, palette;
    std::memcpy(&flags, info.data(), 4);
    std::memcpy(&width, info.data() + 4, 2);
    std::memcpy(&height, info.data() + 6, 2);
    std::memcpy(&palette, info.data() + 12, 2);
    require((flags == 5 || flags == 37) && palette == 0 && width > 0 && height > 0 &&
                width <= 4096 && height <= 4096 && width <= 8 * height && height <= 8 * width,
            "unsupported nonopaque/paletted/dimensioned texture");
    const auto pixels = std::uint64_t(width) * height;
    require(pixels * 2 <= end - found->offset - 16, "texture pixel span exceeds member");
    // Canonical load + RGBA + metadata all admitted before any image allocation.
    proof.allocate(sizeof(zimg::Texture) + pixels * 6 + 512);
    std::unique_ptr<zimg::Texture, void (*)(zimg::Texture *)> image(
        zimg::load(bank.library, pin.entry.c_str()), zimg::free_texture);
    require(image && image->pixels && !image->palette && !image->alpha && image->width == width &&
                image->height == height && !std::ferror(bank.file.get()) &&
                std::ftell(bank.file.get()) == long(found->offset + 16 + pixels * 2),
            "canonical texture decode was partial or substituted");
    std::vector<std::uint8_t> rgba(std::size_t(pixels) * 4);
    zvid::texture_rgba(*image, 0, rgba.data());
    const auto key = mw34::materials::canonical_upload_key(width, height, rgba.data(), 1);
    require(key.hash != 0, "zero surface identity is unsupported");
    platform::integrity::Sha256 source_hash, rgba_hash;
    source_hash.update(image->pixels, std::size_t(pixels) * 2);
    rgba_hash.update(rgba.data(), rgba.size());
    Json detail{{"bank_member", pin.member},
                {"bank_sha256", pin.sha256},
                {"bank_bytes", pin.bytes},
                {"resolved_bank_path", bank.path.u8string()},
                {"source_rgb565_sha256", source_hash.hex()},
                {"upload_rgba_sha256", rgba_hash.hex()},
                {"bank_entry", pin.entry},
                {"bank_entry_index", std::size_t(found - bank.entries.begin())},
                {"bank_entry_offset", found->offset},
                {"mip", pin.mip},
                {"conversion", "opaque-rgb565-upload-v1"}};
    return {key, std::move(detail)};
}
Json parse_json(const std::string &input) {
    require(input.size() <= metadata_limit, "request metadata too large");
    std::vector<std::set<std::string>> keys;
    std::size_t events = 0;
    return Json::parse(input, [&](int depth, Json::parse_event_t event, Json &value) {
        require(depth <= 16 && ++events <= 200000, "JSON complexity limit");
        if (event == Json::parse_event_t::object_start)
            keys.emplace_back();
        if (event == Json::parse_event_t::key)
            require(!keys.empty() && keys.back().insert(value.get<std::string>()).second,
                    "duplicate JSON key");
        if (event == Json::parse_event_t::object_end)
            keys.pop_back();
        return true;
    });
}
void prepare_source(zcls::ZbdReadContext &proof, const std::string &member,
                    const std::string &sha256, std::uint64_t bytes) {
    proof.expected.member = member;
    proof.expected.sha256 = sha256;
    proof.expected.bytes = bytes;
    // Bound the simultaneous request/output JSON, caches, table bookkeeping and
    // source bytes before the canonical source/texture allocations begin.
    proof.allocate(bytes + 128ULL * 1024 * 1024);
}
zutl::Mounts source_mount(const fs::path &root) {
    zutl::Mounts selected;
    selected.read = {fs::canonical(root).u8string()};
    selected.confined = true;
    return selected;
}
Json polygon_identity(const zmod::Model &model) {
    require(model.count(0x10) > 0 && model.count(0x10) <= 4096 && model.polygons,
            "unsupported source polygon count");
    Json result{{"polygon_materials", Json::array()},
                {"material_slots", Json::array()},
                {"texture_directory_slots", Json::array()},
                {"opaque", true}};
    for (std::uint32_t i = 0; i < model.count(0x10); ++i) {
        const auto *material = model.polygons[i].material;
        result["material_slots"].push_back(zmod::materials().index_of(material));
        if (material && (material->alpha != 255 || (material->flags & 6)))
            result["opaque"] = false;
        if (!material || !(material->flags & 1)) {
            result["polygon_materials"].push_back("untextured");
            result["texture_directory_slots"].push_back(nullptr);
        } else {
            require(material->texture && std::memchr(material->texture->name, 0, 20),
                    "unsupported directory name");
            result["polygon_materials"].push_back(material->texture->name);
            result["texture_directory_slots"].push_back(
                std::size_t(material->texture - zimg::textures().entries));
        }
    }
    return result;
}
void append_metadata(Json &array, Json item, std::uint64_t &admitted) {
    // Top-level metadata arrays add four indentation bytes to each item line.
    // Admit the bounded record before retaining it in the document.
    const auto encoded = item.dump(2);
    const auto bytes =
        encoded.size() + 4 * (1 + std::count(encoded.begin(), encoded.end(), '\n')) + 16;
    require(bytes <= metadata_limit - std::min(metadata_limit, admitted),
            "metadata record exceeds output cap");
    admitted += bytes;
    array.push_back(std::move(item));
}
} // namespace

Request read_request(const std::string &input) {
    const auto j = parse_json(input);
    fields(j, {"schema_version", "data_root", "bank_root", "source", "region", "asset_id",
               "surface_materials", "textures"});
    require(number(j.at("schema_version")) == 1, "unsupported request version");
    const auto &source = j.at("source");
    fields(source, {"kind", "member", "sha256", "bytes", "model_slot"});
    require(text(source.at("kind")) == "gamez-zbd-v27", "unsupported source kind");
    Request r;
    r.data_root = fs::u8path(text(j.at("data_root")));
    r.bank_root = fs::u8path(text(j.at("bank_root")));
    r.member = text(source.at("member"));
    r.sha256 = text(source.at("sha256"));
    r.bytes = number(source.at("bytes"));
    const auto slot = number(source.at("model_slot"));
    require(slot < 1048576, "source slot exceeds bound");
    r.model_slot = std::uint32_t(slot);
    r.region = text(j.at("region"));
    r.asset_id = text(j.at("asset_id"));
    r.surface_materials = text(j.at("surface_materials"));
    require(j.at("textures").is_array() && j.at("textures").size() <= 4096,
            "invalid texture selectors");
    for (const auto &t : j.at("textures")) {
        fields(t, {"texture", "member", "sha256", "bytes", "entry", "mip"});
        const auto mip = number(t.at("mip"));
        require(mip == 0, "only explicit mip0 is supported");
        r.textures.push_back({text(t.at("texture")), text(t.at("member")), text(t.at("sha256")),
                              text(t.at("entry")), number(t.at("bytes")), std::uint32_t(mip)});
    }
    validate(r);
    return r;
}

InspectionRequest read_inspection_request(const std::string &input) {
    const auto j = parse_json(input);
    fields(j, {"schema_version", "data_root", "source", "region"});
    require(number(j.at("schema_version")) == 1, "unsupported inspection request version");
    const auto &source = j.at("source");
    fields(source, {"kind", "member", "sha256", "bytes"});
    require(text(source.at("kind")) == "gamez-zbd-v27", "unsupported inspection source kind");
    return {fs::u8path(text(j.at("data_root"))), text(source.at("member")),
            text(source.at("sha256")), text(j.at("region")), number(source.at("bytes"))};
}

std::string inspect_source(const InspectionRequest &r) {
    require(r.region == "t1", "initial inspection supports unchanged Training only");
    require(r.data_root.is_absolute() && member_valid(r.member) && digest_valid(r.sha256) &&
                r.bytes > 0 && r.bytes <= limit && !r.region.empty() && r.region.size() <= 32 &&
                r.region.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789_") ==
                    std::string::npos &&
                r.member == "zbd/" + r.region + "/gamez.zbd",
            "invalid inspection source pin/region");
    auto original = open_file(contained(r.data_root, r.member));
    require(hash_file(original.get(), r.bytes) == r.sha256, "inspection source SHA differs");
    zcls::ZbdReadContext proof(zcls::ZbdReadMode::StrictExport);
    prepare_source(proof, r.member, r.sha256, r.bytes);
    Isolation isolated(source_mount(r.data_root));
    require(zcls::read_zbd(r.member.c_str(), &proof) == 0 && proof.snapshot_verified &&
                !proof.failed,
            "inspection canonical source proof failed");
    require(proof.partitions.size() <= 4096, "inspection partition count exceeds cap");
    Json output{{"schema", "MW34-ground-source-inspection-v1"},
                {"inspection_only", true},
                {"source",
                 {{"kind", "gamez-zbd-v27"},
                  {"member", r.member},
                  {"sha256", r.sha256},
                  {"bytes", r.bytes}}},
                {"region", r.region},
                {"nodes", Json::array()},
                {"models", Json::array()},
                {"partitions", Json::array()}};
    std::uint64_t metadata_bytes = output.dump(2).size();
    proof.allocate(std::uint64_t(proof.node_count) * 16);
    std::vector<std::uint8_t> visited(std::size_t(proof.node_count), 0);
    std::vector<std::uint32_t> pending;
    std::set<std::uint32_t> node_slots, model_slots;
    for (const auto &p : proof.partitions) {
        append_metadata(
            output["partitions"],
            {{"world_node", p.world_node}, {"x", p.x}, {"z", p.z}, {"root_nodes", p.nodes}},
            metadata_bytes);
        for (const auto root : p.nodes)
            pending.push_back(root);
    }
    while (!pending.empty()) {
        const auto slot = pending.back();
        pending.pop_back();
        require(slot < visited.size(), "inspection node outside canonical table");
        if (visited[slot])
            continue;
        visited[slot] = 1;
        node_slots.insert(slot);
        require(node_slots.size() <= 4096, "inspection node count exceeds cap");
        const auto *node = zcls::node_at(std::int32_t(slot));
        require(node && node->cls() && (node->link & zcls::kNodeLive) &&
                    std::memchr(node->name(), 0, 0x24),
                "inspection references unsupported/free node");
        const auto model_slot = proof.node_models[slot];
        if (model_slot >= 0 && node->model && node->model->count(0x10))
            model_slots.insert(std::uint32_t(model_slot));
        for (std::int32_t i = 0; i < node->child_count(); ++i) {
            const auto child = zcls::node_index_of(node->children[i]);
            require(child >= 0 && child < proof.node_count,
                    "inspection child outside canonical table");
            pending.push_back(std::uint32_t(child));
        }
    }
    require(!model_slots.empty() && model_slots.size() <= 4096 && proof.partitions.size() <= 4096,
            "inspection has no source models or exceeds selector cap");
    for (const auto slot : node_slots) {
        const auto *node = zcls::node_at(std::int32_t(slot));
        Json children = Json::array();
        for (std::int32_t i = 0; i < node->child_count(); ++i)
            children.push_back(zcls::node_index_of(node->children[i]));
        append_metadata(output["nodes"],
                        {{"slot", slot},
                         {"name", node->name()},
                         {"class", node->cls()},
                         {"model_slot", proof.node_models[slot]},
                         {"children", std::move(children)}},
                        metadata_bytes);
    }
    for (const auto slot : model_slots) {
        const auto *model = zmod::model_at(std::int32_t(slot));
        auto entry = polygon_identity(*model);
        entry["model_slot"] = slot;
        entry["polygon_count"] = model->count(0x10);
        append_metadata(output["models"], std::move(entry), metadata_bytes);
    }
    require(hash_file(original.get(), r.bytes) == r.sha256, "inspection source changed");
    const auto result = output.dump(2) + "\n";
    require(result.size() <= metadata_limit, "inspection metadata exceeds cap");
    return result;
}

Result export_target(const Request &r) {
    validate(r);
    const auto source_file = contained(r.data_root, r.member);
    auto original = open_file(source_file);
    require(hash_file(original.get(), r.bytes) == r.sha256, "source preflight SHA differs");
    zcls::ZbdReadContext proof(zcls::ZbdReadMode::StrictExport);
    prepare_source(proof, r.member, r.sha256, r.bytes);
    proof.expected.model_slots = {r.model_slot};
    Isolation isolated(source_mount(r.data_root)); // Dies before proof's owning raw allocations.
    require(zcls::read_zbd(r.member.c_str(), &proof) == 0 && proof.snapshot_verified &&
                !proof.failed,
            "canonical source proof failed");
    auto *model = zmod::model_at(std::int32_t(r.model_slot));
    require(model && model->world_source_asset && model->world_source_asset->world &&
                model->world_source_asset->world->model_slot == r.model_slot,
            "source selector was not published");
    const auto uv = cc_mw3_re::native_mesh_uv_hash(*model);
    require(uv && *uv != 0, "unsupported original polygon UV stream");
    Json target{{"surface_materials", r.surface_materials},
                {"asset_id", r.asset_id},
                {"source",
                 {{"kind", "gamez-zbd-v27"},
                  {"member", r.member},
                  {"sha256", r.sha256},
                  {"bytes", r.bytes},
                  {"model_slot", r.model_slot}}},
                {"mesh_uv_hash", hex(*uv)},
                {"polygon_materials", Json::array()},
                {"surface_keys", Json::array()}};
    Json detail{{"schema_version", 1},
                {"region", r.region},
                {"source", target.at("source")},
                {"resolved_source_path", source_file.u8string()},
                {"asset_id", r.asset_id},
                {"mesh_uv_hash", hex(*uv)},
                {"polygons", Json::array()},
                {"nodes", Json::array()},
                {"partitions", Json::array()},
                {"upload_policy",
                 {{"display_format", 6},
                  {"channel_masks", {0xf800, 0x07e0, 0x001f}},
                  {"caps", 0},
                  {"max_width", 4096},
                  {"max_height", 4096},
                  {"format", 1},
                  {"mip", 0}}}};
    std::uint64_t metadata_bytes = detail.dump(2).size() + 128;
    std::map<std::string, std::unique_ptr<Bank>> banks;
    std::map<std::string, std::pair<mw34::materials::SurfaceKey, Json>> cache;
    std::set<std::string> used;
    for (std::uint32_t i = 0; i < model->count(0x10); ++i) {
        const auto *material = model->polygons[i].material;
        Json polygon{{"polygon", i}, {"material_slot", zmod::materials().index_of(material)}};
        require(!material || (material->alpha == 255 && !(material->flags & 6)),
                "nonopaque/cycled source material unsupported");
        if (!material || !(material->flags & 1)) {
            target["polygon_materials"].push_back("untextured");
            target["surface_keys"].push_back(nullptr);
            polygon["texture"] = nullptr;
        } else {
            const auto *texture = material->texture;
            require(texture && std::memchr(texture->name, 0, sizeof texture->name),
                    "source texture is missing/unbounded");
            const std::string name(texture->name);
            const auto pin = std::find_if(r.textures.begin(), r.textures.end(),
                                          [&](const TexturePin &t) { return t.texture == name; });
            require(pin != r.textures.end(), "no explicit exact bank selection for source texture");
            used.insert(name);
            if (!cache.count(name)) {
                auto &bank = banks[pin->member];
                if (!bank)
                    bank = bank_open(r, *pin, proof);
                require(bank->sha256 == pin->sha256 && bank->bytes == pin->bytes,
                        "conflicting bank pins");
                cache.emplace(name, texture_key(*bank, *pin, proof));
            }
            const auto &value = cache.at(name);
            const auto &key = value.first;
            target["polygon_materials"].push_back(name);
            target["surface_keys"].push_back({{"width", key.width},
                                              {"height", key.height},
                                              {"format", key.format},
                                              {"hash", hex(key.hash)}});
            polygon["texture"] = name;
            polygon["texture_directory_slot"] = std::size_t(texture - zimg::textures().entries);
            polygon["selected_source"] = value.second;
        }
        append_metadata(detail["polygons"], std::move(polygon), metadata_bytes);
    }
    require(used.size() == r.textures.size(), "unused texture selector");
    for (std::int32_t i = 0; i < proof.node_count; ++i) {
        auto *node = zcls::node_at(i);
        if (node && node->source_asset == model->world_source_asset)
            append_metadata(detail["nodes"],
                            {{"slot", i}, {"name", node->name()}, {"class", node->cls()}},
                            metadata_bytes);
    }
    proof.allocate(std::uint64_t(proof.node_count) * 16);
    std::vector<std::int8_t> has_selected(std::size_t(proof.node_count), -1);
    struct Visit {
        std::uint32_t slot;
        std::int32_t next;
        bool selected;
    };
    std::vector<Visit> stack;
    const auto contains_selected = [&](std::uint32_t root) {
        stack.clear();
        stack.push_back({root, 0, false});
        while (!stack.empty()) {
            auto &visit = stack.back();
            require(visit.slot < has_selected.size(), "partition source root outside table");
            if (has_selected[visit.slot] >= 0) {
                stack.pop_back();
                continue;
            }
            const auto *node = zcls::node_at(std::int32_t(visit.slot));
            require(node != nullptr, "partition source node is absent");
            if (visit.next < node->child_count()) {
                const auto child = zcls::node_index_of(node->children[visit.next]);
                require(child >= 0 && child < proof.node_count,
                        "partition source child outside table");
                if (has_selected[std::size_t(child)] < 0)
                    stack.push_back({std::uint32_t(child), 0, false});
                else {
                    visit.selected = visit.selected || has_selected[std::size_t(child)];
                    ++visit.next;
                }
            } else {
                has_selected[visit.slot] =
                    visit.selected || node->source_asset == model->world_source_asset;
                stack.pop_back();
            }
        }
        return has_selected[root] != 0;
    };
    for (const auto &p : proof.partitions)
        for (const auto slot : p.nodes) {
            if (contains_selected(slot))
                append_metadata(
                    detail["partitions"],
                    {{"world_node", p.world_node}, {"x", p.x}, {"z", p.z}, {"root_node", slot}},
                    metadata_bytes);
        }
    for (auto &bank : banks)
        require(hash_file(bank.second->file.get(), bank.second->bytes) == bank.second->sha256,
                "bank changed during export");
    require(hash_file(original.get(), r.bytes) == r.sha256, "source changed during export");
    detail["admitted_source_and_allocation_bytes"] = proof.allocated_bytes;
    const auto targets =
        Json{{"schema_version", 1}, {"targets", Json::array({target})}}.dump(2) + "\n";
    const auto receipt = detail.dump(2) + "\n";
    require(targets.size() <= metadata_limit && receipt.size() <= metadata_limit,
            "export metadata exceeds cap");
    return {targets, receipt};
}

namespace {
void write_documents(const std::vector<std::pair<std::string, const std::string *>> &documents,
                     const fs::path &output) {
    for (const auto &item : documents)
        require(item.second->size() <= metadata_limit, "metadata output exceeds cap");
    require(!output.empty() && !fs::exists(output), "output must be fresh");
    auto pending = output;
    pending += ".partial";
    require(fs::create_directory(pending), "fresh output staging is unavailable");
    try {
        for (const auto &item : documents) {
            std::ofstream stream(pending / item.first, std::ios::binary | std::ios::trunc);
            stream.write(item.second->data(), std::streamsize(item.second->size()));
            stream.close();
            require(bool(stream), "metadata write failed");
        }
        require(!fs::exists(output), "output appeared during export");
        fs::rename(pending, output);
    } catch (...) {
        std::error_code ignored;
        for (const auto &item : documents)
            fs::remove(pending / item.first, ignored);
        fs::remove(pending, ignored);
        throw;
    }
}
} // namespace
void write_result(const Result &result, const fs::path &output) {
    write_documents({{"material_targets.json", &result.material_targets},
                     {"export-receipt.json", &result.receipt}},
                    output);
}
void write_inspection(const std::string &inspection, const fs::path &output) {
    write_documents({{"source-inspection.json", &inspection}}, output);
}
} // namespace mw3::ground_targets
