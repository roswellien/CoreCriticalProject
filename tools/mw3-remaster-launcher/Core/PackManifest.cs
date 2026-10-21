using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace MW3RemasterLauncher.Core
{
    /// <summary>Declared payload capabilities; these flags do not prove that files exist.</summary>
    public class PackProvides
    {
        [JsonPropertyName("mechs")]
        public List<string>? Mechs { get; set; }

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
        [JsonPropertyName("schema_version")]
        public int SchemaVersion { get; set; } = 1;

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
