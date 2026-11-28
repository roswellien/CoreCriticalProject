using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace MW3RemasterLauncher.Core
{
    /// <summary>
    /// One problem found by Contract 1 pack checks.
    /// Code is one of the standard problem codes (e.g. "manifest-invalid", "file-undeclared").
    /// </summary>
    public sealed record PackProblem(string Code, string Message)
    {
        public string Line => $"{Code}: {Message}";
    }

    /// <summary>
    /// Checks an unpacked content pack against Contract 1 (docs/packs/contracts.md).
    /// Faithfully mirrors tools/packs/check_pack.py.
    /// </summary>
    public static class PackCheck
    {
        public const string ManifestName = "pack.json";

        // Contract 1: a pack never carries anything that can run.
        private static readonly HashSet<string> ExecutableSuffixes = new(StringComparer.OrdinalIgnoreCase)
        {
            ".bat", ".cmd", ".com", ".dll", ".dylib", ".exe", ".jar", ".js", ".lua", ".msi",
            ".ps1", ".py", ".scr", ".sh", ".so", ".vbs"
        };

        // Reserved Windows device names that cannot be files regardless of extension.
        private static readonly Regex WindowsDeviceName = new(
            @"^(CON|CONIN\$|CONOUT\$|PRN|AUX|NUL|COM[0-9]|LPT[0-9])$",
            RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);

        public const int MaxPathLength = 240;

        // Contract 4: what a visual may dress, and how each kind of target is named.
        private static readonly Regex[] TargetPatterns =
        {
            new(@"\A(mech-model|world):[a-z0-9][a-z0-9_-]{0,31}\z", RegexOptions.CultureInvariant),
            new(@"\Amission:[a-z0-9][a-z0-9_-]{0,31}/[0-9]{1,2}\z", RegexOptions.CultureInvariant),
            new(@"\Agame:mw3\z", RegexOptions.CultureInvariant)
        };

        /// <summary>
        /// Whether a pack-relative path stays inside the pack on every operating system.
        /// </summary>
        public static bool PathIsSafe(string path)
        {
            if (string.IsNullOrEmpty(path) || path.EnumerateRunes().Count() > MaxPathLength || path.Contains('\\'))
                return false;

            var parts = path.Split('/');
            foreach (var part in parts)
            {
                if (part == "" || part == "." || part == "..")
                    return false;

                // Windows drops a trailing dot or space, which would collapse paths.
                if (part.EndsWith('.') || part.EndsWith(' '))
                    return false;

                if (part.Any(c => c < 32 || "<>:\"|?*".Contains(c)))
                    return false;

                var nameBeforeFirstDot = part.Split('.')[0];
                if (WindowsDeviceName.IsMatch(nameBeforeFirstDot))
                    return false;
            }

            return true;
        }

        /// <summary>
        /// Whether a visual target string matches one of the authorized target patterns.
        /// </summary>
        public static bool TargetIsWellFormed(string target)
        {
            return TargetPatterns.Any(pattern => pattern.IsMatch(target));
        }

        /// <summary>
        /// Loads the contract shipped in the launcher, including installed copies outside the repository.
        /// </summary>
        public static JsonDocument LoadSchemaDocument()
        {
            // Use the shipped contract, independent of the pack or working directory.
            var assembly = typeof(PackCheck).Assembly;
            var stream = assembly.GetManifestResourceStream("MW3RemasterLauncher.Core.pack-manifest-v3.schema.json");
            if (stream != null)
            {
                using (stream)
                {
                    return JsonDocument.Parse(stream);
                }
            }

            throw new FileNotFoundException("The launcher is missing its embedded pack-manifest-v3.schema.json contract.");
        }

        /// <summary>
        /// Runs all Contract 1 checks against an unpacked pack folder.
        /// Returns an empty list if the pack is completely valid.
        /// </summary>
        public static List<PackProblem> CheckPack(string packFolder)
        {
            var manifestPath = Path.Combine(packFolder, ManifestName);
            if (!File.Exists(manifestPath))
            {
                return new List<PackProblem> { new("manifest-invalid", $"no {ManifestName}") };
            }

            string text;
            try
            {
                text = new UTF8Encoding(false, true).GetString(File.ReadAllBytes(manifestPath));
            }
            catch (Exception ex)
            {
                return new List<PackProblem> { new("manifest-invalid", ex.Message) };
            }

            // Check for duplicate properties (disallowed in pack manifests)
            JsonDocument parsedDocument;
            try
            {
                parsedDocument = JsonDocument.Parse(text, new JsonDocumentOptions { MaxDepth = 1024 });
                try { PackStorage.ValidateUniqueProperties(parsedDocument.RootElement); }
                catch
                {
                    parsedDocument.Dispose();
                    throw;
                }
            }
            catch (Exception ex)
            {
                return new List<PackProblem> { new("manifest-invalid", ex.Message) };
            }

            using var documentLifetime = parsedDocument;

            var schemaProblems = CheckManifest(parsedDocument.RootElement);

            // If schema validation failed, stop here!
            // Later checks read fields the schema has just said are wrong or missing.
            if (schemaProblems.Count > 0)
            {
                return schemaProblems;
            }

            var problems = new List<PackProblem>();

            // Files table checks
            var root = parsedDocument.RootElement;
            var fileTable = new Dictionary<string, JsonElement>(StringComparer.Ordinal);
            if (root.TryGetProperty("files", out var filesElem) && filesElem.ValueKind == JsonValueKind.Object)
            {
                foreach (var fileProp in filesElem.EnumerateObject())
                {
                    fileTable[fileProp.Name] = fileProp.Value;
                }
            }

            var onDisk = GetFilesOnDisk(packFolder);

            // 1. Files on disk not in files table -> file-undeclared
            foreach (var path in onDisk.Except(fileTable.Keys).OrderBy(p => p, StringComparer.Ordinal))
            {
                problems.Add(new PackProblem("file-undeclared", $"{path} is in the pack but not in files"));
            }

            // 2. Declared files checks
            foreach (var (path, entry) in fileTable.OrderBy(kv => kv.Key, StringComparer.Ordinal))
            {
                if (!PathIsSafe(path))
                {
                    problems.Add(new PackProblem("path-unsafe", $"{path} could leave the pack folder"));
                    continue;
                }

                // pathlib treats a lone leading dot (".exe") as a filename, not a suffix.
                var fileName = path[(path.LastIndexOf('/') + 1)..];
                var lastDot = fileName.LastIndexOf('.');
                var suffix = lastDot > 0 ? fileName[lastDot..] : "";
                if (ExecutableSuffixes.Contains(suffix))
                {
                    problems.Add(new PackProblem("payload-executable", $"{path} is a program or script"));
                }

                if (!onDisk.Contains(path))
                {
                    problems.Add(new PackProblem("file-missing", $"{path} is in files but not in the pack"));
                    continue;
                }

                var fullPath = Path.Combine(packFolder, path.Replace('/', Path.DirectorySeparatorChar));
                try
                {
                    using var content = File.OpenRead(fullPath);
                    var expectedBytes = System.Numerics.BigInteger.Parse(entry.GetProperty("bytes").GetRawText());
                    string expectedSha256 = entry.TryGetProperty("sha256", out var s) ? s.GetString() ?? "" : "";

                    bool sizeMatches = content.Length == expectedBytes;
                    var actualSha256 = Convert.ToHexString(SHA256.HashData(content)).ToLowerInvariant();
                    bool hashMatches = string.Equals(actualSha256, expectedSha256, StringComparison.Ordinal);

                    if (!sizeMatches || !hashMatches)
                    {
                        problems.Add(new PackProblem("file-hash-mismatch", $"{path} differs from its files entry"));
                    }
                }
                catch
                {
                    problems.Add(new PackProblem("file-missing", $"{path} could not be read"));
                }
            }

            // 3. Gameplay payload checks
            if (root.TryGetProperty("gameplay", out var gameplayElem) && gameplayElem.ValueKind == JsonValueKind.Object)
            {
                var gpRoot = gameplayElem.TryGetProperty("root", out var r) ? r.GetString() ?? "" : "";
                if (!PathIsSafe(gpRoot))
                {
                    problems.Add(new PackProblem("path-unsafe", $"gameplay root {gpRoot} could leave the pack folder"));
                }
                else if (!fileTable.ContainsKey($"{gpRoot}/mod.txt"))
                {
                    problems.Add(new PackProblem("gameplay-root-invalid", $"{gpRoot}/mod.txt is not listed in files"));
                }
            }

            // 4. Visuals payload checks
            bool hasGameplay = root.TryGetProperty("gameplay", out var gp) && gp.ValueKind == JsonValueKind.Object;
            if (root.TryGetProperty("visuals", out var visualsElem) && visualsElem.ValueKind == JsonValueKind.Array)
            {
                int index = 0;
                foreach (var visual in visualsElem.EnumerateArray())
                {
                    var target = visual.TryGetProperty("target", out var t) ? t.GetString() ?? "" : "";
                    if (!TargetIsWellFormed(target))
                    {
                        problems.Add(new PackProblem("visual-target-invalid", $"visual {index}: {target}"));
                    }

                    if (visual.TryGetProperty("needs_gameplay", out var ng) && ng.ValueKind == JsonValueKind.True && !hasGameplay)
                    {
                        problems.Add(new PackProblem("visual-needs-gameplay", $"visual {index} needs a gameplay payload this pack does not have"));
                    }

                    if (visual.TryGetProperty("files", out var visualFiles) && visualFiles.ValueKind == JsonValueKind.Object)
                    {
                        foreach (var prop in visualFiles.EnumerateObject().OrderBy(p => p.Name, StringComparer.Ordinal))
                        {
                            var visualFilePath = prop.Value.GetString() ?? "";
                            if (!fileTable.ContainsKey(visualFilePath))
                            {
                                problems.Add(new PackProblem("visual-file-undeclared", $"visual {index}, {prop.Name}: {visualFilePath} is not listed in files"));
                            }
                        }
                    }

                    index++;
                }
            }

            return problems;
        }

        internal static List<PackProblem> CheckManifest(JsonElement manifest)
        {
            using var schema = LoadSchemaDocument();
            return JsonSchemaSubset.FindViolations(manifest, schema.RootElement)
                .Select(violation => new PackProblem(
                    violation.Keyword == "additionalProperties" ? "manifest-unknown-field" : "manifest-invalid",
                    $"{(violation.Path.Length == 0 ? "/" : violation.Path)}: {violation.Message}"))
                .ToList();
        }

        private static HashSet<string> GetFilesOnDisk(string packFolder)
        {
            var found = new HashSet<string>(StringComparer.Ordinal);
            if (!Directory.Exists(packFolder)) return found;

            var dirInfo = new DirectoryInfo(packFolder);
            foreach (var file in dirInfo.EnumerateFiles("*", SearchOption.AllDirectories))
            {
                var relative = Path.GetRelativePath(packFolder, file.FullName).Replace('\\', '/');
                if (!string.Equals(relative, ManifestName, StringComparison.Ordinal))
                {
                    found.Add(relative);
                }
            }

            return found;
        }
    }
}
