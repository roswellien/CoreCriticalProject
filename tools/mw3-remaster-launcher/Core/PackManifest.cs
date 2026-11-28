using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace MW3RemasterLauncher.Core
{
    public class PackFile
    {
        [JsonPropertyName("sha256")] public string Sha256 { get; set; } = "";
        [JsonPropertyName("bytes")] public long Bytes { get; set; }
        [JsonPropertyName("format")] public string? Format { get; set; }
    }

    public class NativePackPayload
    {
        [JsonPropertyName("profile")] public string Profile { get; set; } = "";
        [JsonPropertyName("registry")] public string Registry { get; set; } = "";
        [JsonPropertyName("path_base")] public string PathBase { get; set; } = "";
        [JsonPropertyName("reference_host_sha256")] public string ReferenceHostSha256 { get; set; } = "";
        [JsonPropertyName("required_formats")] public List<string> RequiredFormats { get; set; } = new();
        [JsonPropertyName("required_capabilities")] public Dictionary<string, int> RequiredCapabilities { get; set; } = new();
    }

    /// <summary>
    /// Schema 3 gameplay payload description.
    /// </summary>
    public class PackGameplay
    {
        [JsonPropertyName("root")]
        public string Root { get; set; } = string.Empty;
    }

    /// <summary>
    /// Schema 3 visual dressing description for mechs, worlds, or missions.
    /// </summary>
    public class PackVisual
    {
        [JsonPropertyName("target")]
        public string Target { get; set; } = string.Empty;

        [JsonPropertyName("kind")]
        public string Kind { get; set; } = string.Empty;

        [JsonPropertyName("lod")]
        public int? Lod { get; set; }

        [JsonPropertyName("name")]
        public string? Name { get; set; }

        [JsonPropertyName("needs_gameplay")]
        public bool NeedsGameplay { get; set; }

        [JsonPropertyName("files")]
        public Dictionary<string, string> Files { get; set; } = new(StringComparer.Ordinal);

        [JsonPropertyName("options")]
        public JsonObject? Options { get; set; }
    }

    /// <summary>Declared payload capabilities; these flags do not prove that files exist.</summary>
    public class PackProvides
    {
        [JsonPropertyName("mechs")]
        public List<string>? Mechs { get; set; }

        [JsonPropertyName("weapons")]
        public List<string>? Weapons { get; set; }

        [JsonPropertyName("skins")]
        public List<string>? Skins { get; set; }

        [JsonPropertyName("maps")]
        public List<string>? Maps { get; set; }

        [JsonPropertyName("missions")]
        public List<string>? Missions { get; set; }

        [JsonPropertyName("campaigns")]
        public List<string>? Campaigns { get; set; }

        [JsonPropertyName("world_models")]
        public List<string>? WorldModels { get; set; }

        [JsonPropertyName("textures")]
        public bool Textures { get; set; }

        [JsonPropertyName("normal_maps")]
        public bool NormalMaps { get; set; }

        [JsonPropertyName("audio")]
        public bool Audio { get; set; }

        [JsonPropertyName("cd_music")]
        public bool CdMusic { get; set; }
    }

    /// <summary>Declared dependency metadata, separate from runtime compatibility enforcement.</summary>
    public class PackDependency
    {
        [JsonPropertyName("id")]
        public string Id { get; set; } = string.Empty;

        [JsonPropertyName("min_version")]
        public string? MinVersion { get; set; }

        [JsonPropertyName("optional")]
        public bool Optional { get; set; }
    }

    /// <summary>pack.json metadata plus nonserialized launcher discovery/selection state.</summary>
    /// <remarks>
    /// Id identifies a pack; it is not an authenticated publisher identity or a safe path.
    /// DirectoryPath and the other JsonIgnore properties belong to the local launcher.
    /// Deserializing this type does not validate dependency versions or payload contents.
    /// </remarks>
    public class PackManifest
    {
        [JsonIgnore]
        public bool HasGameplay => SchemaVersion == 3 && Gameplay != null;

        // Existing packs without an explicit target are MW3 packs only.
        [JsonPropertyName("game_id")]
        public string GameId { get; set; } = GameCatalog.Mw3;

        [JsonPropertyName("schema_version")]
        public int SchemaVersion { get; set; } = 1;

        [JsonPropertyName("native_payload")]
        public NativePackPayload? NativePayload { get; set; }

        [JsonPropertyName("gameplay")]
        public PackGameplay? Gameplay { get; set; }

        [JsonPropertyName("visuals")]
        public List<PackVisual>? Visuals { get; set; }

        [JsonPropertyName("files")]
        public Dictionary<string, PackFile>? Files { get; set; }

        [JsonPropertyName("id")]
        public string Id { get; set; } = string.Empty;

        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("version")]
        public string Version { get; set; } = "1.0.0";

        [JsonPropertyName("author")]
        public string Author { get; set; } = "Unknown";

        [JsonPropertyName("homepage")]
        public string? Homepage { get; set; }

        [JsonPropertyName("description")]
        public string Description { get; set; } = string.Empty;

        [JsonPropertyName("category")]
        public string Category { get; set; } = "General";

        [JsonPropertyName("min_engine_version")]
        public string? MinEngineVersion { get; set; }

        [JsonPropertyName("dependencies")]
        public List<PackDependency>? Dependencies { get; set; }

        [JsonPropertyName("conflicts")]
        public List<string>? Conflicts { get; set; }

        [JsonPropertyName("provides")]
        public PackProvides? Provides { get; set; }

        [JsonIgnore]
        public string? UpdateSource { get; set; }

        /// <summary>
        /// Summarizes the items or payloads provided by this pack.
        /// </summary>
        [JsonIgnore]
        public string ProvidesSummary
        {
            get
            {
                var items = new List<string>();
                if (Provides != null)
                {
                    if (Provides.Mechs != null && Provides.Mechs.Count > 0)
                        items.Add($"Mechs: {string.Join(", ", Provides.Mechs)}");
                    if (Provides.Weapons != null && Provides.Weapons.Count > 0)
                        items.Add($"Weapons: {string.Join(", ", Provides.Weapons)}");
                    if (Provides.Skins != null && Provides.Skins.Count > 0)
                        items.Add($"Skins: {string.Join(", ", Provides.Skins)}");
                    if (Provides.Maps != null && Provides.Maps.Count > 0)
                        items.Add($"Maps: {string.Join(", ", Provides.Maps)}");
                    if (Provides.Missions != null && Provides.Missions.Count > 0)
                        items.Add($"Missions: {string.Join(", ", Provides.Missions)}");
                    if (Provides.Campaigns != null && Provides.Campaigns.Count > 0)
                        items.Add($"Campaigns: {string.Join(", ", Provides.Campaigns)}");
                    if (Provides.WorldModels != null && Provides.WorldModels.Count > 0)
                        items.Add($"World models: {string.Join(", ", Provides.WorldModels)}");
                    if (Provides.Textures)
                        items.Add("Textures");
                    if (Provides.NormalMaps)
                        items.Add("Normal maps");
                    if (Provides.Audio)
                        items.Add("Audio");
                    if (Provides.CdMusic)
                        items.Add("CD music");
                }

                if (items.Count == 0)
                {
                    if (Gameplay != null && Visuals != null && Visuals.Count > 0)
                        items.Add("Gameplay and visuals");
                    else if (Gameplay != null)
                        items.Add("Gameplay");
                    else if (Visuals != null && Visuals.Count > 0)
                        items.Add("Visuals");
                    else
                        items.Add("Content");
                }

                return string.Join(" • ", items);
            }
        }

        [JsonIgnore]
        public string RuntimeLabel
        {
            get
            {
                if (SchemaVersion == 3)
                {
                    var summary = ProvidesSummary;
                    var updateSource = string.IsNullOrWhiteSpace(UpdateSource) ? "no update source" : UpdateSource;
                    return $"{summary} — {updateSource}";
                }
                if (SchemaVersion == 2)
                {
                    return NativePayload?.Profile == ChassisPack.Profile ? "Additional mechs — choose in Mech Lab" :
                           NativePayload?.Profile == SkinPack.Profile ? "Additional skins — choose in Mech Lab" :
                           NativePayload?.Profile == CinematicPack.Profile ? "Cinematics — AVI replacements or launcher movie library" :
                           NativePayload?.Profile == UiPack.Profile ? "HUD/menu artwork — original layout and input" :
                           NativePayload?.Profile == MusicPack.Profile ? "Soundtrack — original game music controls" :
                           NativePayload?.Profile == "prepared-environment-v1" ? "Environment textures, normals and lighting — playtest pending" :
                           "Native mech candidates — gameplay validation pending";
                }
                return "";
            }
        }

        // Local state
        [JsonIgnore]
        public string DirectoryPath { get; set; } = string.Empty;

        [JsonIgnore]
        public string? PreviewImagePath { get; set; }

        [JsonIgnore]
        public bool IsEnabled { get; set; } = true;

        [JsonIgnore]
        public int Priority { get; set; } = 0;

        [JsonIgnore]
        public bool IsOfficial { get; set; } = false;
    }
}
