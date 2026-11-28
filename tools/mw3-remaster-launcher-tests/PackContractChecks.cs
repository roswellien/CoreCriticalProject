using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Text.Json;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncherTests
{
    /// <summary>
    /// Verification and regression checks for Contract 1 pack checks and schema 3 pack lifecycle (#646).
    /// Tests Contract 1 check against tests/fixtures/packs/expected.json, install of valid packs,
    /// rejection of broken packs with correct problem codes, staging cleanup, uninstall,
    /// UI display ("what it provides" and "no update source"), and --pack-library argument passing.
    /// </summary>
    public static class PackContractChecks
    {
        private static void Assert(bool condition, string message)
        {
            if (!condition) throw new Exception(message);
        }

        public static string FindRepositoryRoot()
        {
            for (var dir = new DirectoryInfo(AppDomain.CurrentDomain.BaseDirectory); dir != null; dir = dir.Parent)
            {
                var marker = Path.Combine(dir.FullName, "tests", "fixtures", "packs", "expected.json");
                if (File.Exists(marker)) return dir.FullName;
            }

            // Also try current directory
            for (var dir = new DirectoryInfo(Directory.GetCurrentDirectory()); dir != null; dir = dir.Parent)
            {
                var marker = Path.Combine(dir.FullName, "tests", "fixtures", "packs", "expected.json");
                if (File.Exists(marker)) return dir.FullName;
            }

            throw new FileNotFoundException("Cannot find repository root containing tests/fixtures/packs/expected.json.");
        }

        private static void CreateArchiveFromDirectory(string sourceFolder, string targetZipPath)
        {
            if (File.Exists(targetZipPath)) File.Delete(targetZipPath);
            using var archive = ZipFile.Open(targetZipPath, ZipArchiveMode.Create);
            var dirInfo = new DirectoryInfo(sourceFolder);
            foreach (var file in dirInfo.EnumerateFiles("*", SearchOption.AllDirectories))
            {
                var relativePath = Path.GetRelativePath(sourceFolder, file.FullName).Replace('\\', '/');
                var entry = archive.CreateEntry(relativePath);
                using var entryStream = entry.Open();
                using var fileStream = file.OpenRead();
                fileStream.CopyTo(entryStream);
            }
        }

        public static void CheckEmbeddedSchema()
        {
            var temporary = Directory.CreateTempSubdirectory("MW3EmbeddedPack-");
            try
            {
                using var schema = PackCheck.LoadSchemaDocument();
                Assert(schema.RootElement.GetProperty("properties").GetProperty("schema_version")
                    .GetProperty("const").GetInt32() == 3, "Embedded schema is not version 3.");
                File.WriteAllText(Path.Combine(temporary.FullName, "pack.json"),
                    """{"schema_version":3,"game_id":"mw3","id":"embedded-test","name":"Embedded test","version":"1.0.0","files":{}}""");
                Assert(PackCheck.CheckPack(temporary.FullName).Count == 0,
                    "Installed launcher could not validate using its embedded schema.");
                Console.WriteLine("Embedded schema loaded and validated an authored pack.");
            }
            finally { temporary.Delete(recursive: true); }
        }

        private static void CheckSchemaSubset()
        {
            void Check(string valueJson, string schemaJson, params string[] keywords)
            {
                using var value = JsonDocument.Parse(valueJson);
                using var schema = JsonDocument.Parse(schemaJson);
                var actual = JsonSchemaSubset.FindViolations(value.RootElement, schema.RootElement)
                    .Select(violation => violation.Keyword);
                Assert(actual.SequenceEqual(keywords), $"Schema subset mismatch for {valueJson} against {schemaJson}.");
            }
            Check("1.0", """{"type":"integer"}""", "type");
            Check("1e0", """{"type":"integer"}""", "type");
            Check("18446744073709551616", """{"type":"integer","minimum":0}""");
            Check("0.0", """{"enum":[0,1]}""", "enum");
            Check("true", """{"type":"number"}""", "type");
            Check("true", """{"const":1}""", "const");
            Check("[]", """{"type":"array","minItems":1}""", "minItems");
            Check("[1,1]", """{"maxItems":1,"uniqueItems":true}""", "maxItems", "uniqueItems");
            Check("[[1],[true]]", """{"uniqueItems":true}""", "uniqueItems");
            Check("[1,1.0]", """{"uniqueItems":true}""");
            Check("[false]", """{"items":{"type":"string"}}""", "type");
            Check("9007199254740992", """{"minimum":9007199254740993}""", "minimum");
            Check("[[9007199254740993],[9007199254740992.0]]", """{"uniqueItems":true}""");
            Check("-1", """{"minimum":0}""", "minimum");
            Check("2", """{"maximum":1}""", "maximum");
            Check("{}", """{"required":["name"]}""", "required");
            Check("{\"typo\":1}", """{"additionalProperties":false}""", "additionalProperties");
            Check("{\"value\":1}", """{"additionalProperties":{"type":"string"}}""", "type");
            Check("\"ab\"", """{"minLength":3,"pattern":"^[0-9]+$"}""", "minLength", "pattern");
            Check("\"ab\"", """{"maxLength":1}""", "maxLength");
            Check("\"\U0001F600\"", """{"minLength":1,"maxLength":1}""");
            Check("1", """{"$ref":"#/$defs/text","$defs":{"text":{"type":"string"}}}""", "type");
            Assert(!PackCheck.TargetIsWellFormed("game:mw3\n"), "Target grammar accepted a trailing newline.");
            Assert(!PackCheck.PathIsSafe("a/CON.txt"), "Path grammar accepted a device name.");
            Assert(PackCheck.PathIsSafe(new string('a', 239) + "\U0001F600"), "Path length counted UTF-16 units.");
            using var unsupported = JsonDocument.Parse("""{"not_a_keyword":true}""");
            using var item = JsonDocument.Parse("1");
            try { JsonSchemaSubset.FindViolations(item.RootElement, unsupported.RootElement); }
            catch (UnsupportedSchemaException) { return; }
            throw new Exception("Unknown schema keywords were silently ignored.");
        }

        private static void CheckLegacyManifestBehavior()
        {
            var temporary = Directory.CreateTempSubdirectory("MW3LegacyManifest-");
            try
            {
                var path = Path.Combine(temporary.FullName, "pack.json");
                void Reject(string json, string message)
                {
                    File.WriteAllText(path, json);
                    try { PackStorage.ReadManifest(path); }
                    catch (InvalidDataException error)
                    {
                        Assert(error.Message == message, $"Legacy message changed: '{error.Message}'.");
                        return;
                    }
                    throw new Exception("Invalid legacy manifest was accepted.");
                }
                foreach (var version in new[] { 1, 2 })
                {
                    Reject($"{{\"schema_version\":{version},\"id\":\"../bad\"}}", "Invalid pack ID.");
                    Reject($"{{\"schema_version\":{version},\"id\":\"test\",\"id\":\"test\"}}", "Duplicate JSON property.");
                }
                Reject("""{"schema_version":2,"id":"test"}""", "Unsupported prepared-native pack contract.");
                Reject("""{"schema_version":4,"id":"test"}""", "Unsupported pack schema.");
                File.WriteAllText(path, """{"schema_version":1,"id":"legacy.test","unknown":"still allowed"}""");
                Assert(PackStorage.ReadManifest(path).SchemaVersion == 1, "Schema 1 gained schema 3 restrictions.");
                var legacyExtras = "\"gameplay\":42,\"visuals\":false,\"provides\":{\"skins\":false,\"weapons\":1}";
                File.WriteAllText(path, "{\"schema_version\":1,\"id\":\"legacy.test\"," + legacyExtras + "}");
                Assert(PackStorage.ReadManifest(path).Gameplay == null, "Schema 1 stopped ignoring unknown metadata.");
                File.WriteAllText(path, "{\"schema_version\":2,\"id\":\"legacy.test\"," + legacyExtras +
                    ",\"native_payload\":{\"profile\":\"prepared-native-v1\",\"path_base\":\"pack-root\",\"registry\":\"models/models.json\"}," +
                    "\"files\":{\"models/models.json\":{\"bytes\":0,\"sha256\":\"" + new string('0', 64) + "\"}}}");
                Assert(PackStorage.ReadManifest(path).SchemaVersion == 2, "Schema 2 stopped ignoring unknown metadata.");
                File.WriteAllText(path, """{"schema_version":3,"id":"truncated",""");
                var rejectedTruncated = false;
                try { PackStorage.ReadManifest(path); }
                catch (InvalidDataException error)
                {
                    rejectedTruncated = true;
                    Assert(error.Message.StartsWith("manifest-invalid:", StringComparison.Ordinal),
                        "Truncated schema 3 manifest did not report its problem code.");
                }
                Assert(rejectedTruncated, "Truncated schema 3 manifest was accepted.");
                File.WriteAllText(path, "{");
                try { PackStorage.ReadManifest(path); }
                catch (JsonException) { return; }
                throw new Exception("Legacy JSON syntax exception changed.");
            }
            finally { temporary.Delete(recursive: true); }
        }

        public static void Run()
        {
            Console.WriteLine("Running schema 3 pack contract and lifecycle checks...");
            var repoRoot = FindRepositoryRoot();
            var fixturesDir = Path.Combine(repoRoot, "tests", "fixtures", "packs");
            var expectedJsonPath = Path.Combine(fixturesDir, "expected.json");
            Assert(File.Exists(expectedJsonPath), "expected.json fixture missing: " + expectedJsonPath);

            using var doc = JsonDocument.Parse(File.ReadAllText(expectedJsonPath));
            var root = doc.RootElement;

            // 1. Verify Contract 1 PackCheck on all valid fixtures
            Console.WriteLine("Checking valid pack fixtures against Contract 1...");
            foreach (var validElem in root.GetProperty("valid").EnumerateArray())
            {
                var name = validElem.GetString()!;
                var packDir = Path.Combine(fixturesDir, "valid", name);
                Assert(Directory.Exists(packDir), "Valid fixture folder missing: " + packDir);

                var problems = PackCheck.CheckPack(packDir);
                Assert(problems.Count == 0,
                    $"Valid fixture '{name}' failed pack check with {problems.Count} problem(s): " +
                    string.Join("; ", problems.Select(p => p.Line)));
            }

            // 2. Verify Contract 1 PackCheck on all broken fixtures
            Console.WriteLine("Checking broken pack fixtures against Contract 1 expected problem codes...");
            foreach (var prop in root.GetProperty("broken").EnumerateObject())
            {
                var name = prop.Name;
                var expectedCode = prop.Value.GetProperty("code").GetString()!;
                var foundBy = prop.Value.GetProperty("found_by").GetString()!;
                var packDir = Path.Combine(fixturesDir, "broken", name);
                Assert(Directory.Exists(packDir), "Broken fixture folder missing: " + packDir);

                var problems = PackCheck.CheckPack(packDir);
                if (foundBy == "pack-check")
                {
                    var actualCodes = problems.Select(problem => problem.Code)
                        .Distinct(StringComparer.Ordinal).ToArray();
                    Assert(actualCodes.SequenceEqual(new[] { expectedCode }),
                        $"Fixture '{name}' expected only '{expectedCode}', got: " +
                        string.Join("; ", problems.Select(problem => problem.Line)));
                }
                else if (foundBy == "runtime")
                {
                    // Runtime-only problems are well-formed packs that pass pack-check
                    Assert(problems.Count == 0,
                        $"Fixture '{name}' marked found_by 'runtime' failed pack check: " +
                        string.Join("; ", problems.Select(p => p.Line)));
                }
                else throw new Exception($"Unknown found_by '{foundBy}' in fixture '{name}'.");
            }

            // The expectation file must cover every shared pack, including newly added fixtures.
            foreach (var group in new[] { "valid", "broken" })
            {
                var expectedNames = group == "valid"
                    ? root.GetProperty(group).EnumerateArray().Select(item => item.GetString()!)
                    : root.GetProperty(group).EnumerateObject().Select(item => item.Name);
                var actualNames = Directory.GetDirectories(Path.Combine(fixturesDir, group))
                    .Select(Path.GetFileName).OrderBy(name => name, StringComparer.Ordinal);
                Assert(actualNames.SequenceEqual(expectedNames.OrderBy(name => name, StringComparer.Ordinal)),
                    $"expected.json does not cover every {group} fixture directory.");
            }

            CheckEmbeddedSchema();
            CheckSchemaSubset();
            CheckLegacyManifestBehavior();

            // 3. Test pack installation, UI display, staging cleanup, and uninstallation
            Console.WriteLine("Testing schema 3 pack installation, staging cleanup, and uninstallation...");
            var testTempDir = Path.Combine(Path.GetTempPath(), "MW3Schema3Checks-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(testTempDir);
            try
            {
                var packManager = new PackManager(testTempDir);
                var installedValidPacks = new List<PackManifest>();

                // Install valid packs
                foreach (var validElem in root.GetProperty("valid").EnumerateArray())
                {
                    var name = validElem.GetString()!;
                    var packDir = Path.Combine(fixturesDir, "valid", name);
                    var archivePath = Path.Combine(testTempDir, $"{name}.mw3pack");
                    CreateArchiveFromDirectory(packDir, archivePath);

                    var installed = packManager.InstallPack(archivePath);
                    Assert(installed != null, $"Install returned null for valid pack: {name}");
                    Assert(installed!.SchemaVersion == 3, $"Installed pack schema version is {installed.SchemaVersion}, expected 3");
                    Assert(Directory.Exists(installed.DirectoryPath), $"Installed pack directory does not exist: {installed.DirectoryPath}");

                    // Check UI display: provides summary and "no update source"
                    Assert(!string.IsNullOrWhiteSpace(installed.ProvidesSummary),
                        $"Pack '{installed.Id}' provides summary was empty");
                    Assert(installed.RuntimeLabel.Contains("no update source"),
                        $"Pack '{installed.Id}' RuntimeLabel '{installed.RuntimeLabel}' missing 'no update source' label");
                    Assert(installed.RuntimeLabel.StartsWith(installed.ProvidesSummary, StringComparison.Ordinal),
                        $"Pack '{installed.Id}' RuntimeLabel '{installed.RuntimeLabel}' does not start with ProvidesSummary '{installed.ProvidesSummary}'");

                    installedValidPacks.Add(installed);
                    var reloaded = new PackManager(testTempDir);
                    reloaded.RefreshPacks();
                    Assert(reloaded.DiscoveryErrors.Count == 0 && reloaded.Packs.Any(pack => pack.Id == installed.Id),
                        $"Installed pack '{installed.Id}' was not rediscovered.");
                }

                // Verify rejection of broken packs and staging cleanup
                foreach (var prop in root.GetProperty("broken").EnumerateObject())
                {
                    var name = prop.Name;
                    var expectedCode = prop.Value.GetProperty("code").GetString()!;
                    var foundBy = prop.Value.GetProperty("found_by").GetString()!;
                    var packDir = Path.Combine(fixturesDir, "broken", name);
                    var archivePath = Path.Combine(testTempDir, $"broken-{name}.mw3pack");
                    CreateArchiveFromDirectory(packDir, archivePath);

                    if (foundBy == "runtime")
                    {
                        var installed = packManager.InstallPack(archivePath);
                        Assert(Directory.Exists(installed.DirectoryPath),
                            $"Runtime-only fixture '{name}' did not install.");
                        packManager.UninstallPack(installed);
                    }
                    else if (foundBy == "pack-check")
                    {
                        bool rejected = false;
                        string rejectedMessage = "";
                        try
                        {
                            packManager.InstallPack(archivePath);
                        }
                        catch (InvalidDataException ex)
                        {
                            rejected = true;
                            rejectedMessage = ex.Message;
                        }

                        Assert(rejected, $"Broken pack '{name}' was accepted during InstallPack but should have been rejected.");
                        Assert(rejectedMessage.Contains(expectedCode),
                            $"Broken pack '{name}' rejection message '{rejectedMessage}' did not contain expected code '{expectedCode}'.");

                        // Verify pack is never present under its final directory name
                        using var brokenManifest = JsonDocument.Parse(File.ReadAllText(Path.Combine(packDir, "pack.json")));
                        var finalDir = Path.Combine(packManager.ModsRoot, brokenManifest.RootElement.GetProperty("id").GetString()!);
                        Assert(!Directory.Exists(finalDir),
                            $"Broken pack '{name}' left final directory after failed installation: {finalDir}");

                        // Verify staging directory cleanup: no .staging-* folders remain
                        var stagingFolders = Directory.GetDirectories(packManager.ModsRoot, ".staging-*");
                        Assert(stagingFolders.Length == 0,
                            $"Staging cleanup failed for broken pack '{name}': leftover folders: " + string.Join(", ", stagingFolders));
                    }
                }

                // 4. Test Uninstall of a schema 3 pack
                var packToUninstall = installedValidPacks.First();
                var packPathBeforeUninstall = packToUninstall.DirectoryPath;
                Assert(Directory.Exists(packPathBeforeUninstall), "Pack directory missing before uninstall");

                var uninstalled = packManager.UninstallPack(packToUninstall);
                Assert(uninstalled, "UninstallPack returned false");
                Assert(!Directory.Exists(packPathBeforeUninstall),
                    $"UninstallPack did not delete the pack directory: {packPathBeforeUninstall}");
                Assert(!packManager.Packs.Contains(packToUninstall),
                    "UninstallPack did not remove the pack from PackManager.Packs");

                // 5. Verify the launcher writes nothing to <write dir>\mods\
                var writeDir = Path.Combine(testTempDir, "mw3-re", "profiles", "native-preview");
                var writeDirMods = Path.Combine(writeDir, "mods");
                Assert(!Directory.Exists(writeDirMods),
                    $"Launcher wrote to runtime write dir mods folder: {writeDirMods}");

                // 6. Test --pack-library argument passing logic
                // Case A: With at least one schema 3 gameplay pack installed (we have 'gameplay-and-visuals' or 'gameplay-only' installed)
                bool hasGameplayInstalled = NativeGameRunner.HasInstalledGameplayPack(testTempDir, out var packLibraryFolder);
                Assert(hasGameplayInstalled, "HasInstalledGameplayPack returned false when schema 3 gameplay pack was installed");
                Assert(string.Equals(Path.GetFullPath(packLibraryFolder), Path.GetFullPath(packManager.ModsRoot), StringComparison.OrdinalIgnoreCase),
                    $"packLibraryFolder '{packLibraryFolder}' does not match mods root '{packManager.ModsRoot}'");

                Assert(NativeGameRunner.PackLibraryArguments(testTempDir).SequenceEqual(
                    new[] { "--pack-library", packManager.ModsRoot }),
                    "Native launch arguments did not name the folder holding installed packs.");

                // Case B: In a separate clean folder with only visuals-only installed or empty
                var visualsOnlyTempDir = Path.Combine(Path.GetTempPath(), "MW3VisualsOnlyChecks-" + Guid.NewGuid().ToString("N"));
                Directory.CreateDirectory(visualsOnlyTempDir);
                try
                {
                    var visualsManager = new PackManager(visualsOnlyTempDir);
                    var visualsArchive = Path.Combine(visualsOnlyTempDir, "visuals-only.mw3pack");
                    CreateArchiveFromDirectory(Path.Combine(fixturesDir, "valid", "visuals-only"), visualsArchive);
                    visualsManager.InstallPack(visualsArchive);

                    var legacyFolder = Path.Combine(visualsManager.ModsRoot, "legacy");
                    Directory.CreateDirectory(legacyFolder);
                    File.WriteAllText(Path.Combine(legacyFolder, "pack.json"),
                        """{"schema_version":1,"id":"legacy","gameplay":{"root":"gameplay"}}""");
                    Assert(NativeGameRunner.PackLibraryArguments(visualsOnlyTempDir).Count == 0,
                        "Visual-only and legacy packs added --pack-library to native arguments.");
                    // Staging, rollback and mismatched identities must not count as installations.
                    foreach (var folder in new[] { ".staging-test", ".rollback-test", "wrong-id" })
                    {
                        var path = Path.Combine(visualsManager.ModsRoot, folder);
                        Directory.CreateDirectory(path);
                        File.Copy(Path.Combine(fixturesDir, "valid", "gameplay-only", "pack.json"),
                            Path.Combine(path, "pack.json"));
                    }
                    Assert(NativeGameRunner.PackLibraryArguments(visualsOnlyTempDir).Count == 0,
                        "A staging, rollback or mismatched folder enabled --pack-library.");

                    bool hasGameplayVisualsOnly = NativeGameRunner.HasInstalledGameplayPack(visualsOnlyTempDir, out _);
                    Assert(!hasGameplayVisualsOnly,
                        "HasInstalledGameplayPack returned true when only a visuals-only pack was installed; must be false!");

                    // Empty library
                    var emptyTempDir = Path.Combine(Path.GetTempPath(), "MW3EmptyLibraryChecks-" + Guid.NewGuid().ToString("N"));
                    Directory.CreateDirectory(emptyTempDir);
                    try
                    {
                        Assert(NativeGameRunner.PackLibraryArguments(emptyTempDir).Count == 0,
                            "An empty library added --pack-library to native arguments.");
                        bool hasGameplayEmpty = NativeGameRunner.HasInstalledGameplayPack(emptyTempDir, out _);
                        Assert(!hasGameplayEmpty,
                            "HasInstalledGameplayPack returned true for empty library; must be false!");
                    }
                    finally
                    {
                        if (Directory.Exists(emptyTempDir)) Directory.Delete(emptyTempDir, true);
                    }
                }
                finally
                {
                    if (Directory.Exists(visualsOnlyTempDir)) Directory.Delete(visualsOnlyTempDir, true);
                }
            }
            finally
            {
                if (Directory.Exists(testTempDir)) Directory.Delete(testTempDir, true);
            }

            Console.WriteLine("All schema 3 pack contract checks passed.");
        }
    }
}
