#nullable enable
using System.Diagnostics;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using MW3RemasterLauncher.Core;

static class NativePreviewSigningChecks
{
    public static void Run()
    {
        var repoRoot = FindRepositoryRoot();
        var launcherDir = Path.Combine(repoRoot, "tools", "mw3-remaster-launcher");
        var checksProject = Path.Combine(repoRoot, "tools", "mw3-remaster-launcher-tests", "LauncherChecks.csproj");
        var signWindowsScript = Path.Combine(launcherDir, "sign_windows.ps1");
        var signPreviewScript = Path.Combine(launcherDir, "sign_native_preview.ps1");
        var buildInstallerScript = Path.Combine(launcherDir, "build_installer.ps1");
        var powerShell = FindPowerShellExecutable();
        var signedPeSource = FindSignedDotNetExecutable();
        var unsignedPeSource = FindUnsignedLauncherChecksExecutable();

        var work = Path.Combine(Path.GetTempPath(), "MW3 preview signing checks " + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(work);
        try
        {
            var stubFailTool = Path.Combine(work, "failing-signtool.cmd");
            File.WriteAllText(stubFailTool, "@echo off\r\nexit /b 1\r\n", Encoding.ASCII);
            var stubNoopTool = Path.Combine(work, "noop-signtool.cmd");
            File.WriteAllText(stubNoopTool, "@echo off\r\nexit /b 0\r\n", Encoding.ASCII);
            var stubDlib = Path.Combine(work, "Azure.CodeSigning.Dlib.dll");
            File.WriteAllText(stubDlib, "authored fixture dlib", Encoding.ASCII);
            var stubMetadata = Path.Combine(work, "signing-metadata.json");
            File.WriteAllText(
                stubMetadata,
                """{"Endpoint":"https://wus2.codesigning.azure.net","CodeSigningAccountName":"fixture-acct","CertificateProfileName":"fixture-profile"}""",
                Encoding.ASCII);

            CheckSignWindowsDirect(powerShell, signWindowsScript, signedPeSource, unsignedPeSource,
                stubFailTool, stubNoopTool, stubDlib, stubMetadata, work);

            var signedPreviewOutput = CheckSignNativePreviewPositive(powerShell, signPreviewScript, checksProject,
                signedPeSource, stubFailTool, stubDlib, stubMetadata, work);

            CheckSignNativePreviewRejections(powerShell, signPreviewScript, checksProject,
                signedPeSource, unsignedPeSource, stubFailTool, stubDlib, stubMetadata, work);

            CheckBuildInstallerHelpersAndGate(powerShell, buildInstallerScript, signPreviewScript,
                signedPreviewOutput, signedPeSource, unsignedPeSource, work);

            Console.WriteLine("Native preview signing, re-pinning and installer PE gate checks passed.");
        }
        finally
        {
            DeleteTreeWithJunctions(work);
        }
    }

    private static void CheckSignWindowsDirect(
        string powerShell,
        string signWindowsScript,
        string signedPeSource,
        string unsignedPeSource,
        string stubFailTool,
        string stubNoopTool,
        string stubDlib,
        string stubMetadata,
        string work)
    {
        var dir = Path.Combine(work, "sign-windows-direct");
        Directory.CreateDirectory(dir);

        var signedCopy = Path.Combine(dir, "signed.exe");
        File.Copy(signedPeSource, signedCopy);
        var validReceipt = Path.Combine(dir, "valid-receipt.json");
        var validRun = RunPowerShellFile(powerShell, signWindowsScript,
            "-File", signedCopy,
            "-SignTool", stubFailTool,
            "-Dlib", stubDlib,
            "-Metadata", stubMetadata,
            "-ReceiptPath", validReceipt);
        Check(validRun.ExitCode == 0 && File.Exists(validReceipt),
            "sign_windows.ps1 did not retain an already valid timestamped signature: " + validRun.FormatOutput());
        var receiptJson = JsonNode.Parse(File.ReadAllText(validReceipt))!.AsObject();
        var firstFile = receiptJson["files"]!.AsArray()[0]!.AsObject();
        Check(firstFile["retained_existing_signature"]!.GetValue<bool>() &&
              firstFile["timestamped"]!.GetValue<bool>() &&
              firstFile["before_sha256"]!.GetValue<string>() == firstFile["sha256"]!.GetValue<string>(),
            "sign_windows.ps1 receipt did not record retained timestamped signature identity.");

        var unsignedCopy = Path.Combine(dir, "unsigned.exe");
        File.Copy(unsignedPeSource, unsignedCopy);
        foreach (var (name, toolPath) in new[] { ("failing-signtool", stubFailTool), ("noop-signtool", stubNoopTool) })
        {
            var receipt = Path.Combine(dir, $"reject-{name}.json");
            var run = RunPowerShellFile(powerShell, signWindowsScript,
                "-File", unsignedCopy,
                "-SignTool", toolPath,
                "-Dlib", stubDlib,
                "-Metadata", stubMetadata,
                "-ReceiptPath", receipt);
            Check(run.ExitCode != 0 && !File.Exists(receipt),
                $"sign_windows.ps1 unexpectedly accepted unsigned binary with {name}.");
        }
    }

    private static string CheckSignNativePreviewPositive(
        string powerShell,
        string signPreviewScript,
        string checksProject,
        string signedPeSource,
        string stubFailTool,
        string stubDlib,
        string stubMetadata,
        string work)
    {
        var inputDir = Path.Combine(work, "preview-positive-in");
        CreateAuthoredRuntimeFixture(inputDir, signedPeSource, staleBuildId: true, out var obsBeforeBytes);

        var outputDir = Path.Combine(work, "preview-positive-out");
        var receiptPath = Path.Combine(work, "preview-positive.signatures.json");
        // Omit -ChecksOutputDirectory here so default temp BaseOutputPath allocation + cleanup is exercised.
        var run = RunPowerShellFile(powerShell, signPreviewScript,
            "-RuntimeDirectory", inputDir,
            "-OutputDirectory", outputDir,
            "-WindowsSignTool", stubFailTool,
            "-SigningDlib", stubDlib,
            "-SigningMetadata", stubMetadata,
            "-ReceiptPath", receiptPath,
            "-LauncherChecksProject", checksProject);

        Check(run.ExitCode == 0, "sign_native_preview.ps1 positive run failed: " + run.FormatOutput());
        Check(!File.Exists(Path.Combine(outputDir, ".incomplete")),
            "sign_native_preview.ps1 left .incomplete marker after passing checks.");
        Check(File.Exists(receiptPath) && !File.Exists(Path.Combine(outputDir, Path.GetFileName(receiptPath))),
            "Signing receipt was missing or written inside OutputDirectory.");

        var obsAfterBytes = File.ReadAllBytes(Path.Combine(outputDir, "metadata", "build-observation.json"));
        Check(obsBeforeBytes.AsSpan().SequenceEqual(obsAfterBytes),
            "metadata/build-observation.json changed during runtime signing.");

        var outManifestPath = Path.Combine(outputDir, "runtime.json");
        var rawManifestBytes = File.ReadAllBytes(outManifestPath);
        Check(!(rawManifestBytes.Length >= 3 && rawManifestBytes[0] == 0xEF &&
                rawManifestBytes[1] == 0xBB && rawManifestBytes[2] == 0xBF),
            "Updated runtime.json was written with a UTF-8 BOM.");

        var outJson = JsonNode.Parse(Encoding.UTF8.GetString(rawManifestBytes))!.AsObject();
        var signedExeHash = ComputeLowerSha256(Path.Combine(outputDir, "bin", "mw3.exe"));
        var expectedBuildId = "mw3-re-" + signedExeHash;
        Check(outJson["provenance"]!["build_id"]!.GetValue<string>() == expectedBuildId,
            "Updated runtime.json provenance.build_id did not match signed mw3.exe SHA-256.");
        Check(outJson["dependencies"] is JsonArray deps && deps.Count == 1,
            "Updated runtime.json flattened single-item dependencies array.");
        Check(outJson["capabilities"]!["controller-profile"] is JsonArray singleCap && singleCap.Count == 1 &&
              outJson["capabilities"]!["input-bindings"] is JsonArray multiCap && multiCap.Count == 2,
            "Updated runtime.json flattened capability version arrays.");

        var contract = Mw3ReRuntimeContract.ReadStructure(outputDir);
        Check(contract.BuildId == expectedBuildId,
            "Mw3ReRuntimeContract.ReadStructure did not observe updated build_id.");

        var verifierExe = Path.Combine(AppContext.BaseDirectory, "LauncherChecks.exe");
        if (File.Exists(verifierExe))
        {
            var verifyCli = RunProcess(verifierExe, new[] { "--verify-native-preview", outputDir });
            Check(verifyCli.ExitCode == 0,
                "LauncherChecks --verify-native-preview rejected valid signed closure: " + verifyCli.FormatOutput());
        }

        return outputDir;
    }

    private static void CheckSignNativePreviewRejections(
        string powerShell,
        string signPreviewScript,
        string checksProject,
        string signedPeSource,
        string unsignedPeSource,
        string stubFailTool,
        string stubDlib,
        string stubMetadata,
        string work)
    {
        var sharedChecksOut = Path.Combine(work, "shared-reject-checks-bin") + "/";
        var preSignCases = new (string Name, Action<string, string> Mutate)[]
        {
            ("tampered-pin", (root, _) =>
            {
                File.WriteAllText(Path.Combine(root, "profile.json"), "{\"tampered\":true}");
            }),
            ("extra-unpinned-file", (root, _) =>
            {
                File.WriteAllText(Path.Combine(root, "extra-unpinned.txt"), "unexpected");
            }),
            ("traversal-pin-key", (root, _) =>
            {
                var manifestPath = Path.Combine(root, "runtime.json");
                var doc = JsonNode.Parse(File.ReadAllText(manifestPath))!.AsObject();
                doc["files"]!.AsObject()["../escape.dll"] = new JsonObject
                {
                    ["bytes"] = 4,
                    ["sha256"] = new string('a', 64)
                };
                File.WriteAllText(manifestPath, doc.ToJsonString());
            }),
            ("junction-in-input", (root, scratchRoot) =>
            {
                var target = Path.Combine(scratchRoot, "junction-target");
                Directory.CreateDirectory(target);
                File.WriteAllText(Path.Combine(target, "linked.txt"), "linked");
                CreateDirectoryJunction(Path.Combine(root, "linked-dir"), target);
            })
        };

        foreach (var (name, mutate) in preSignCases)
        {
            var caseWork = Path.Combine(work, "presign-" + name);
            var inputDir = Path.Combine(caseWork, "in");
            var outputDir = Path.Combine(caseWork, "out");
            var receiptPath = Path.Combine(caseWork, "receipt.json");
            CreateAuthoredRuntimeFixture(inputDir, signedPeSource, staleBuildId: false, out _);
            mutate(inputDir, caseWork);

            var run = RunPowerShellFile(powerShell, signPreviewScript,
                "-RuntimeDirectory", inputDir,
                "-OutputDirectory", outputDir,
                "-WindowsSignTool", stubFailTool,
                "-SigningDlib", stubDlib,
                "-SigningMetadata", stubMetadata,
                "-ReceiptPath", receiptPath,
                "-LauncherChecksProject", checksProject,
                "-ChecksOutputDirectory", sharedChecksOut);

            Check(run.ExitCode != 0 && !Directory.Exists(outputDir) && !File.Exists(receiptPath),
                $"Pre-sign check '{name}' unexpectedly accepted input or created output: " + run.FormatOutput());
        }

        // Negative signing run with unsigned PE must fail and preserve .incomplete marker.
        var unsignedWork = Path.Combine(work, "unsigned-pe-run");
        var unsignedIn = Path.Combine(unsignedWork, "in");
        var unsignedOut = Path.Combine(unsignedWork, "out");
        var unsignedReceipt = Path.Combine(unsignedWork, "receipt.json");
        CreateAuthoredRuntimeFixture(unsignedIn, unsignedPeSource, staleBuildId: false, out _);

        var unsignedRun = RunPowerShellFile(powerShell, signPreviewScript,
            "-RuntimeDirectory", unsignedIn,
            "-OutputDirectory", unsignedOut,
            "-WindowsSignTool", stubFailTool,
            "-SigningDlib", stubDlib,
            "-SigningMetadata", stubMetadata,
            "-ReceiptPath", unsignedReceipt,
            "-LauncherChecksProject", checksProject,
            "-ChecksOutputDirectory", sharedChecksOut);

        Check(unsignedRun.ExitCode != 0 && File.Exists(Path.Combine(unsignedOut, ".incomplete")),
            "Unsigned PE signing failure either exited 0 or removed .incomplete.");
    }

    private static void CheckBuildInstallerHelpersAndGate(
        string powerShell,
        string buildInstallerScript,
        string signPreviewScript,
        string signedPreviewOutput,
        string signedPeSource,
        string unsignedPeSource,
        string work)
    {
        // Direct execution without -Compiler/-OutputDirectory must fail non-zero.
        var directRun = RunPowerShellFile(powerShell, buildInstallerScript);
        Check(directRun.ExitCode != 0,
            "build_installer.ps1 unexpectedly succeeded without -Compiler and -OutputDirectory.");

        var helperDir = Path.Combine(work, "installer-helper-checks");
        Directory.CreateDirectory(helperDir);

        var staleBuildIdDir = Path.Combine(helperDir, "stale-build-id");
        CopyDirectoryRecursive(signedPreviewOutput, staleBuildIdDir);
        var staleManifestPath = Path.Combine(staleBuildIdDir, "runtime.json");
        var staleJson = JsonNode.Parse(File.ReadAllText(staleManifestPath))!.AsObject();
        staleJson["provenance"]!["build_id"] = "mw3-re-" + new string('0', 64);
        File.WriteAllText(staleManifestPath, staleJson.ToJsonString());

        var repinnedUnsignedDir = Path.Combine(helperDir, "repinned-unsigned");
        CreateAuthoredRuntimeFixture(repinnedUnsignedDir, unsignedPeSource, staleBuildId: false, out _);

        var signedStateHarness = Path.Combine(helperDir, "check-signed-state.ps1");
        File.WriteAllText(signedStateHarness, $$"""
$ErrorActionPreference = 'Stop'
. '{{EscapeSingleQuoted(buildInstallerScript)}}'
if (-not (Test-NativePreviewSignedState -Root '{{EscapeSingleQuoted(signedPreviewOutput)}}')) {
    throw 'Expected Test-NativePreviewSignedState to accept signed closure'
}
if (Test-NativePreviewSignedState -Root '{{EscapeSingleQuoted(staleBuildIdDir)}}') {
    throw 'Expected Test-NativePreviewSignedState to reject stale build_id'
}
if (Test-NativePreviewSignedState -Root '{{EscapeSingleQuoted(repinnedUnsignedDir)}}') {
    throw 'Expected Test-NativePreviewSignedState to reject unsigned PE'
}
""", Encoding.UTF8);

        var signedStateRun = RunPowerShellFile(powerShell, signedStateHarness);
        Check(signedStateRun.ExitCode == 0,
            "build_installer.ps1 helper state checks failed: " + signedStateRun.FormatOutput());

        // Table-driven Assert-AllBinariesSigned gate across root, NativePreview\, and Tools\PlannerPython\.
        var gateCases = new (string Name, bool ExpectPass, Action<string> Populate)[]
        {
            ("all-signed-timestamped", true, root =>
            {
                SeedSignedPublishTree(root, signedPeSource);
            }),
            ("unsigned-root-exe", false, root =>
            {
                SeedSignedPublishTree(root, signedPeSource);
                File.Copy(unsignedPeSource, Path.Combine(root, "Core Critical Launcher.exe"), overwrite: true);
            }),
            ("unsigned-native-preview-exe", false, root =>
            {
                SeedSignedPublishTree(root, signedPeSource);
                File.Copy(unsignedPeSource, Path.Combine(root, "NativePreview", "bin", "mw3.exe"), overwrite: true);
            }),
            ("unsigned-native-preview-dll", false, root =>
            {
                SeedSignedPublishTree(root, signedPeSource);
                File.Copy(unsignedPeSource, Path.Combine(root, "NativePreview", "bin", "SDL3_sound.dll"), overwrite: true);
            }),
            ("unsigned-planner-python-pyd", false, root =>
            {
                SeedSignedPublishTree(root, signedPeSource);
                File.Copy(unsignedPeSource, Path.Combine(root, "Tools", "PlannerPython", "_ctypes.pyd"), overwrite: true);
            }),
            ("junction-in-planner-python", false, root =>
            {
                SeedSignedPublishTree(root, signedPeSource);
                var linkTarget = Path.Combine(Path.GetDirectoryName(root)!, "gate-link-target");
                Directory.CreateDirectory(linkTarget);
                File.Copy(signedPeSource, Path.Combine(linkTarget, "extra.dll"));
                CreateDirectoryJunction(Path.Combine(root, "Tools", "PlannerPython", "linked"), linkTarget);
            })
        };

        foreach (var (name, expectPass, populate) in gateCases)
        {
            var caseDir = Path.Combine(helperDir, "gate-" + name);
            var publishRoot = Path.Combine(caseDir, "publish");
            Directory.CreateDirectory(publishRoot);
            populate(publishRoot);

            var gateHarness = Path.Combine(caseDir, "run-gate.ps1");
            File.WriteAllText(gateHarness, $$"""
$ErrorActionPreference = 'Stop'
. '{{EscapeSingleQuoted(buildInstallerScript)}}'
Assert-AllBinariesSigned -Root '{{EscapeSingleQuoted(publishRoot)}}'
""", Encoding.UTF8);

            var run = RunPowerShellFile(powerShell, gateHarness);
            if (expectPass)
            {
                Check(run.ExitCode == 0, $"Assert-AllBinariesSigned rejected valid case '{name}': " + run.FormatOutput());
            }
            else
            {
                Check(run.ExitCode != 0, $"Assert-AllBinariesSigned failed to block '{name}'.");
            }
        }
    }

    private static void SeedSignedPublishTree(string root, string signedPeSource)
    {
        var previewBin = Path.Combine(root, "NativePreview", "bin");
        var pythonDir = Path.Combine(root, "Tools", "PlannerPython");
        var unshieldDir = Path.Combine(root, "Tools", "Unshield");
        Directory.CreateDirectory(previewBin);
        Directory.CreateDirectory(pythonDir);
        Directory.CreateDirectory(unshieldDir);

        File.Copy(signedPeSource, Path.Combine(root, "Core Critical Launcher.exe"));
        File.Copy(signedPeSource, Path.Combine(previewBin, "mw3.exe"));
        File.Copy(signedPeSource, Path.Combine(previewBin, "SDL3_sound.dll"));
        File.Copy(signedPeSource, Path.Combine(pythonDir, "python314.dll"));
        File.Copy(signedPeSource, Path.Combine(pythonDir, "_ctypes.pyd"));
        File.Copy(signedPeSource, Path.Combine(unshieldDir, "unshield.exe"));
    }

    private static void CreateAuthoredRuntimeFixture(
        string root,
        string peSource,
        bool staleBuildId,
        out byte[] observationBytes)
    {
        var binDir = Path.Combine(root, "bin");
        var metadataDir = Path.Combine(root, "metadata");
        Directory.CreateDirectory(binDir);
        Directory.CreateDirectory(metadataDir);

        var exePath = Path.Combine(binDir, "mw3.exe");
        File.Copy(peSource, exePath, overwrite: true);

        var profilePath = Path.Combine(root, "profile.json");
        File.WriteAllText(profilePath, """{"authored":true}""", new UTF8Encoding(false));

        var obsPath = Path.Combine(metadataDir, "build-observation.json");
        observationBytes = Encoding.UTF8.GetBytes("""{"kind":"mw3-re-local-observation","note":"authored-witness"}""");
        File.WriteAllBytes(obsPath, observationBytes);

        var files = new JsonObject();
        foreach (var rel in new[] { "bin/mw3.exe", "metadata/build-observation.json", "profile.json" })
        {
            var full = Path.Combine(root, rel.Replace('/', Path.DirectorySeparatorChar));
            var bytes = File.ReadAllBytes(full);
            files[rel] = new JsonObject
            {
                ["bytes"] = bytes.Length,
                ["sha256"] = Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant()
            };
        }

        var exeHash = ComputeLowerSha256(exePath);
        var manifest = new JsonObject
        {
            ["schema_version"] = 2,
            ["engine"] = "mw3-re",
            ["roles"] = new JsonObject
            {
                ["executable"] = "bin/mw3.exe",
                ["profile"] = "profile.json"
            },
            ["dependencies"] = new JsonArray("metadata/build-observation.json"),
            ["files"] = files,
            ["provenance"] = new JsonObject
            {
                ["source_commit"] = new string('a', 40),
                ["build_id"] = staleBuildId ? "mw3-re-" + new string('0', 64) : "mw3-re-" + exeHash,
                ["builder"] = "fixture-builder"
            },
            ["capabilities"] = new JsonObject
            {
                ["controller-profile"] = new JsonArray(1),
                ["input-bindings"] = new JsonArray(1, 2)
            }
        };

        File.WriteAllText(Path.Combine(root, "runtime.json"), manifest.ToJsonString(), new UTF8Encoding(false));
    }

    private static string FindRepositoryRoot()
    {
        foreach (var anchor in new[] { AppContext.BaseDirectory, Environment.CurrentDirectory })
        {
            var dir = new DirectoryInfo(Path.GetFullPath(anchor));
            while (dir != null)
            {
                if (File.Exists(Path.Combine(dir.FullName, "tools", "mw3-remaster-launcher", "sign_native_preview.ps1")) &&
                    File.Exists(Path.Combine(dir.FullName, "tools", "mw3-remaster-launcher-tests", "LauncherChecks.csproj")))
                {
                    return dir.FullName;
                }
                dir = dir.Parent;
            }
        }
        throw new DirectoryNotFoundException("Could not locate repository root containing launcher signing scripts.");
    }

    private static string FindPowerShellExecutable()
    {
        var pathEnv = Environment.GetEnvironmentVariable("PATH") ?? "";
        foreach (var entry in pathEnv.Split(Path.PathSeparator, StringSplitOptions.RemoveEmptyEntries))
        {
            foreach (var name in new[] { "pwsh.exe", "pwsh" })
            {
                var candidate = Path.Combine(entry.Trim(), name);
                if (File.Exists(candidate)) return candidate;
            }
        }
        return "powershell.exe";
    }

    private static string FindSignedDotNetExecutable()
    {
        var pathEnv = Environment.GetEnvironmentVariable("PATH") ?? "";
        foreach (var entry in pathEnv.Split(Path.PathSeparator, StringSplitOptions.RemoveEmptyEntries))
        {
            var candidate = Path.Combine(entry.Trim(), "dotnet.exe");
            if (File.Exists(candidate)) return candidate;
        }
        var programFiles = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "dotnet", "dotnet.exe");
        if (File.Exists(programFiles)) return programFiles;
        throw new FileNotFoundException("Could not locate signed dotnet.exe fixture.");
    }

    private static string FindUnsignedLauncherChecksExecutable()
    {
        var candidate = Path.Combine(AppContext.BaseDirectory, "LauncherChecks.exe");
        if (File.Exists(candidate)) return candidate;
        throw new FileNotFoundException("Could not locate LauncherChecks.exe in test output directory: " + AppContext.BaseDirectory);
    }

    private static void CreateDirectoryJunction(string linkPath, string targetPath)
    {
        var cmd = RunProcess("cmd.exe", new[] { "/c", "mklink", "/J", linkPath, targetPath });
        if (cmd.ExitCode != 0)
        {
            throw new IOException("Could not create test directory junction: " + cmd.FormatOutput());
        }
    }

    private static void CopyDirectoryRecursive(string source, string destination)
    {
        Directory.CreateDirectory(destination);
        foreach (var dir in Directory.GetDirectories(source, "*", SearchOption.AllDirectories))
        {
            Directory.CreateDirectory(Path.Combine(destination, Path.GetRelativePath(source, dir)));
        }
        foreach (var file in Directory.GetFiles(source, "*", SearchOption.AllDirectories))
        {
            var rel = Path.GetRelativePath(source, file);
            var target = Path.Combine(destination, rel);
            Directory.CreateDirectory(Path.GetDirectoryName(target)!);
            File.Copy(file, target, overwrite: true);
        }
    }

    private static void DeleteTreeWithJunctions(string root)
    {
        if (!Directory.Exists(root)) return;
        foreach (var dir in Directory.GetDirectories(root, "*", SearchOption.AllDirectories)
                     .OrderByDescending(path => path.Length))
        {
            if (Directory.Exists(dir) &&
                (File.GetAttributes(dir) & FileAttributes.ReparsePoint) != 0)
            {
                Directory.Delete(dir);
            }
        }
        Directory.Delete(root, recursive: true);
    }

    private static string ComputeLowerSha256(string path)
    {
        using var stream = File.OpenRead(path);
        return Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
    }

    private static string EscapeSingleQuoted(string value) => value.Replace("'", "''");

    private static ProcessOutput RunPowerShellFile(string shellExe, string scriptPath, params string[] scriptArgs)
    {
        var allArgs = new List<string> { "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", scriptPath };
        allArgs.AddRange(scriptArgs);
        return RunProcess(shellExe, allArgs);
    }

    private static ProcessOutput RunProcess(string fileName, IEnumerable<string> arguments)
    {
        var info = new ProcessStartInfo(fileName)
        {
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true
        };
        foreach (var arg in arguments)
        {
            info.ArgumentList.Add(arg);
        }
        using var process = Process.Start(info)!;
        var stdoutTask = process.StandardOutput.ReadToEndAsync();
        var stderrTask = process.StandardError.ReadToEndAsync();
        process.WaitForExit();
        Task.WaitAll(stdoutTask, stderrTask);
        return new ProcessOutput(process.ExitCode, stdoutTask.Result, stderrTask.Result);
    }

    private static void Check(bool condition, string message)
    {
        if (!condition) throw new Exception(message);
    }

    private readonly record struct ProcessOutput(int ExitCode, string StdOut, string StdErr)
    {
        public string FormatOutput() => $"exit={ExitCode}; stdout={StdOut.Trim()}; stderr={StdErr.Trim()}";
    }
}
