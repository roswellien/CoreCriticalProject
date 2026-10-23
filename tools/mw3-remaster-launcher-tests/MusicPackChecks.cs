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
            string Archive(string id, string source = "music/2.wav", bool corrupt = false)
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
                var registry = JsonSerializer.SerializeToUtf8Bytes(new { schema_version = 2, payload_profile = MusicPack.Profile,
                    tracks = new[] { new { cd_track = 2, source }, new { cd_track = 3, source = "music/3.wav" } } });
                var members = new Dictionary<string, byte[]> { [MusicPack.Registry] = registry, ["music/2.wav"] = wav, ["music/3.wav"] = wav };
                var files = members.ToDictionary(x => x.Key, x => new { bytes = x.Value.Length, sha256 = Convert.ToHexString(SHA256.HashData(x.Value)).ToLowerInvariant() });
                var archive = Path.Combine(root, Guid.NewGuid() + ".mw3pack");
                using var zip = ZipFile.Open(archive, ZipArchiveMode.Create);
                void Write(string name, byte[] bytes) { using var stream = zip.CreateEntry(name).Open(); stream.Write(bytes); }
                Write("pack.json", JsonSerializer.SerializeToUtf8Bytes(new { schema_version = 2, id, name = id, provides = new { cd_music = true },
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
