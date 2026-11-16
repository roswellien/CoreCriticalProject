using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;
using MW3RemasterLauncher.Core;

static class MusicPackChecks
{
    public static void Run()
    {
        var root = Path.Combine(Path.GetTempPath(), "MW3 soundtrack checks " + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            string Archive(string id, string source = "music/2.wav", bool corrupt = false, byte variant = 0, string version = "1.0.0")
            {
                // Short authored PCM silence, never original music.
                var wav = new byte[52];
                using (var output = new BinaryWriter(new MemoryStream(wav)))
                {
                    output.Write("RIFF"u8); output.Write(44); output.Write("WAVEfmt "u8);
                    output.Write(16); output.Write((short)1); output.Write((short)2);
                    output.Write(44100); output.Write(176400); output.Write((short)4); output.Write((short)16);
                    output.Write("data"u8); output.Write(8); output.Write(0L);
                }
                wav[^1] = variant;
                var registry = JsonSerializer.SerializeToUtf8Bytes(new { schema_version = 2, payload_profile = MusicPack.Profile,
                    tracks = new[] { new { cd_track = 2, source }, new { cd_track = 3, source = "music/3.wav" } } });
                var members = new Dictionary<string, byte[]> { [MusicPack.Registry] = registry, ["music/2.wav"] = wav, ["music/3.wav"] = wav };
                var files = members.ToDictionary(x => x.Key, x => new { bytes = x.Value.Length, sha256 = Convert.ToHexString(SHA256.HashData(x.Value)).ToLowerInvariant() });
                var archive = Path.Combine(root, Guid.NewGuid() + ".mw3pack");
                using var zip = ZipFile.Open(archive, ZipArchiveMode.Create);
                void Write(string name, byte[] bytes) { using var stream = zip.CreateEntry(name).Open(); stream.Write(bytes); }
                Write("pack.json", JsonSerializer.SerializeToUtf8Bytes(new { schema_version = 2, id, version, name = id, provides = new { cd_music = true },
                    native_payload = new { profile = MusicPack.Profile, registry = MusicPack.Registry, path_base = "pack-root" }, files }));
                if (corrupt) members["music/2.wav"][0] ^= 1;
                foreach (var member in members) Write(member.Key, member.Value);
                return archive;
            }
            void Reject(Action action)
            {
                try { action(); } catch (InvalidDataException) { return; }
                throw new Exception("Invalid soundtrack was accepted.");
            }
            var manager = new PackManager(root);
            var first = manager.InstallPack(Archive("test.music.first"));
            var second = manager.InstallPack(Archive("test.music.second"));
            manager.RefreshPacks(new List<string> { first.Id, second.Id });
            var nativeWrite = Path.Combine(root, "native-profile");
            if (MusicPack.StageForNative(manager.GetActivePackDirectories(), nativeWrite) != 2)
                throw new Exception("Enabled soundtrack was not staged for MW3-RE.");
            var stagedTrack = Path.Combine(nativeWrite, "music", "track02.wav");
            var stagedBytes = File.ReadAllBytes(stagedTrack);
            if (!stagedBytes.SequenceEqual(File.ReadAllBytes(Path.Combine(first.DirectoryPath, "music/2.wav"))) ||
                MusicPack.StageForNative(manager.GetActivePackDirectories(), nativeWrite) != 0 ||
                !stagedBytes.SequenceEqual(File.ReadAllBytes(stagedTrack)))
                throw new Exception("Soundtrack staging changed an already-current profile track.");
            var updated = manager.InstallPack(Archive(first.Id, variant: 1, version: "2.0.0"));
            manager.RefreshPacks(new List<string> { first.Id, second.Id });
            if (MusicPack.StageForNative(manager.GetActivePackDirectories(), nativeWrite) != 2 ||
                !File.ReadAllBytes(stagedTrack).SequenceEqual(File.ReadAllBytes(Path.Combine(updated.DirectoryPath, "music/2.wav"))))
                throw new Exception("Updating the active soundtrack pack did not replace launcher-staged tracks.");
            var stagedRecord = JsonNode.Parse(File.ReadAllText(Path.Combine(nativeWrite, "music", "launcher-staged.json")))!;
            if (stagedRecord["tracks"]![0]!["pack_id"]!.GetValue<string>() != first.Id ||
                stagedRecord["tracks"]![0]!["pack_version"]!.GetValue<string>() != "2.0.0")
                throw new Exception("Launcher-staged record omitted pack identity or version.");
            if (MusicPack.StageForNative(Array.Empty<string>(), nativeWrite) != 0 ||
                File.Exists(stagedTrack) || File.Exists(Path.Combine(nativeWrite, "music", "track03.wav")))
                throw new Exception("Disabling the soundtrack pack did not remove launcher-staged tracks.");
            var conflictingWrite = Path.Combine(root, "native-profile-with-user-music");
            var userMusic = Path.Combine(conflictingWrite, "music", "track02.wav");
            Directory.CreateDirectory(Path.GetDirectoryName(userMusic)!);
            File.WriteAllText(userMusic, "authored user soundtrack");
            if (MusicPack.StageForNative(manager.GetActivePackDirectories(), conflictingWrite) != 1 ||
                File.ReadAllText(userMusic) != "authored user soundtrack" ||
                !File.Exists(Path.Combine(conflictingWrite, "music", "track03.wav")))
                throw new Exception("Soundtrack staging replaced profile music or failed to add an unoccupied track.");
            if (MusicPack.StageForNative(Array.Empty<string>(), conflictingWrite) != 0 ||
                File.ReadAllText(userMusic) != "authored user soundtrack" ||
                File.Exists(Path.Combine(conflictingWrite, "music", "track03.wav")))
                throw new Exception("Disabling the pack did not preserve user music while removing staged tracks.");
            var changedWrite = Path.Combine(root, "native-profile-changed-staged-track");
            if (MusicPack.StageForNative(manager.GetActivePackDirectories(), changedWrite) != 2)
                throw new Exception("Could not stage tracks for changed-file preservation check.");
            var changedTrack = Path.Combine(changedWrite, "music", "track02.wav");
            File.Delete(changedTrack); // Model an editor replacing the staged copy with a user-owned file.
            File.WriteAllText(changedTrack, "user replaced launcher-staged track");
            MusicPack.StageForNative(Array.Empty<string>(), changedWrite);
            if (File.ReadAllText(changedTrack) != "user replaced launcher-staged track" ||
                File.Exists(Path.Combine(changedWrite, "music", "track03.wav")))
                throw new Exception("Reconciliation touched a staged file after it changed into user music.");
            var corruptRecordWrite = Path.Combine(root, "native-profile-corrupt-stage-record");
            if (MusicPack.StageForNative(manager.GetActivePackDirectories(), corruptRecordWrite) != 2)
                throw new Exception("Could not stage tracks for corrupt-record preservation check.");
            var corruptRecord = Path.Combine(corruptRecordWrite, "music", "launcher-staged.json");
            File.WriteAllText(corruptRecord, "not valid staging metadata");
            MusicPack.StageForNative(Array.Empty<string>(), corruptRecordWrite);
            if (!File.Exists(Path.Combine(corruptRecordWrite, "music", "track02.wav")) ||
                !File.Exists(Path.Combine(corruptRecordWrite, "music", "track03.wav")))
                throw new Exception("A corrupt staging record caused unknown profile music to be removed.");
            JsonObject Profile() => JsonNode.Parse("{\"native\":{\"local_cd_audio\":true,\"content_capabilities\":{\"soundtrack\":[1]}}}")!.AsObject();
            var profile = Profile();
            MusicPack.Apply(profile, manager.GetActivePackDirectories(), true);
            if (!profile["native"]!["music_inputs"]!["tracks"]![0]!["source"]!.GetValue<string>().StartsWith(first.DirectoryPath))
                throw new Exception("Soundtrack priority failed.");
            if (manager.InspectConflicts().Single().WinningPackName != first.Name) throw new Exception("Soundtrack conflict report failed.");
            MusicPack.Apply(profile, manager.GetActivePackDirectories(), false);
            if (profile["native"]!["local_cd_audio"]!.GetValue<bool>() || profile["native"]!["music_inputs"] != null)
                throw new Exception("Music off did not clear bindings.");
            MusicPack.Apply(profile, Array.Empty<string>(), true);
            if (profile["native"]!["local_cd_audio"]!.GetValue<bool>()) throw new Exception("Missing optional pack blocks silence.");
            profile["native"]!["stock_soundtrack"] = new JsonObject { ["schema_version"] = 1, ["root"] = second.DirectoryPath };
            MusicPack.Apply(profile, Array.Empty<string>(), true);
            if (!profile["native"]!["local_cd_audio"]!.GetValue<bool>() ||
                !profile["native"]!["music_inputs"]!["tracks"]![0]!["source"]!.GetValue<string>().StartsWith(second.DirectoryPath))
                throw new Exception("Bundled default soundtrack incorrectly requires an enabled pack.");
            MusicPack.Apply(profile, new[] { first.DirectoryPath }, true);
            if (!profile["native"]!["music_inputs"]!["tracks"]![0]!["source"]!.GetValue<string>().StartsWith(first.DirectoryPath))
                throw new Exception("Bundled soundtrack overrode the selected replacement pack.");
            MusicPack.Apply(profile, Array.Empty<string>(), false);
            if (profile["native"]!["local_cd_audio"]!.GetValue<bool>() || profile["native"]!["music_inputs"] != null)
                throw new Exception("Bundled soundtrack ignored the music-off preference.");
            var original = Path.Combine(root, "OriginalGame", "Music");
            Directory.CreateDirectory(original);
            File.WriteAllText(Path.Combine(original, "1-02. MechWarrior 3 - Track 01.flac"), "authored source placeholder");
            File.WriteAllText(Path.Combine(original, "1-03. MechWarrior 3 - Track 02.flac"), "authored source placeholder");
            MusicPack.Apply(profile, Array.Empty<string>(), true, Path.GetDirectoryName(original));
            if (!profile["native"]!["local_cd_audio"]!.GetValue<bool>() ||
                !profile["native"]!["music_inputs"]!["tracks"]![0]!["source"]!.GetValue<string>().StartsWith(original))
                throw new Exception("Original soundtrack incorrectly requires a replacement pack.");
            MusicPack.Apply(profile, Array.Empty<string>(), false, Path.GetDirectoryName(original));
            if (profile["native"]!["local_cd_audio"]!.GetValue<bool>() || profile["native"]!["music_inputs"] != null)
                throw new Exception("Original soundtrack ignores the user's off choice.");
            var stockRegistry = Path.Combine(second.DirectoryPath, MusicPack.Registry);
            var savedRegistry = File.ReadAllBytes(stockRegistry);
            File.WriteAllText(stockRegistry, "corrupt");
            Reject(() => MusicPack.Apply(profile, Array.Empty<string>(), true));
            File.WriteAllBytes(stockRegistry, savedRegistry);
            Reject(() => manager.InstallPack(Archive(first.Id, "../escape.wav")));
            Reject(() => manager.InstallPack(Archive(first.Id, corrupt: true)));
            File.WriteAllText(Path.Combine(first.DirectoryPath, "music/2.wav"), "tampered");
            Reject(() => MusicPack.Apply(Profile(), new[] { first.DirectoryPath }, true));
            manager.UninstallPack(second);
            Console.WriteLine("Soundtrack install, priority, disable, absence, corruption and containment checks passed.");
        }
        finally { Directory.Delete(root, true); }
    }
}
