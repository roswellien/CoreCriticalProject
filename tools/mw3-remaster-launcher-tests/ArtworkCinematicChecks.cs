#nullable enable
using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using MW3RemasterLauncher.Core;

static class ArtworkCinematicChecks
{
    public static void Run()
    {
        foreach (var malformed in new[] { "null", "[]", "{\"ui-artwork\":[]}", "{\"ui-artwork\":[true]}",
            "{\"ui-artwork\":[1.0]}", "{\"ui-artwork\":[-1]}", "{\"ui-artwork\":[1,1]}" })
        {
            try
            {
                RuntimeContentCapabilities.Advertised(new JsonObject { ["content_capabilities"] = JsonNode.Parse(malformed) });
                throw new Exception("Malformed runtime capability table was accepted.");
            }
            catch (InvalidDataException) { }
        }
        foreach (var successor in new[] {
            "879408f40d492459b7168f5bab6ba7f3cf89f19d1f12feac3bc0cf21154150a4",
            "dee5e15e02ae18539a3f5b7a89f1e1abac55a2afd964717c28fb900351f85f0a",
            "3aae1c6eb38fe299904823f082754f1339628e2ef6dbf338f8a935bc63aed5c0" })
        {
            var legacy = new JsonObject { ["executable_sha256"] = successor.ToUpperInvariant() };
            RuntimeContentCapabilities.Require(legacy, new NativePackPayload { Profile = UiPack.Profile }, "legacy.hud");
            RuntimeContentCapabilities.Require(legacy, new NativePackPayload { Profile = CinematicPack.Profile }, "legacy.movie");
        }
        var root = Path.Combine(Path.GetTempPath(), "MW3 artwork checks " + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            const string host = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
            var manager = new PackManager(root);
            string Archive(string id, string profile, string registry, Dictionary<string, byte[]> resources, Dictionary<string,string> formats)
            {
                var files = resources.ToDictionary(p => p.Key, p => new { bytes = p.Value.Length,
                    sha256 = Convert.ToHexString(SHA256.HashData(p.Value)).ToLowerInvariant(), format = formats.GetValueOrDefault(p.Key) });
                var path = Path.Combine(root, Guid.NewGuid()+".mw3pack");
                using var zip = ZipFile.Open(path, ZipArchiveMode.Create);
                void Write(string name, byte[] content) { using var output = zip.CreateEntry(name).Open(); output.Write(content); }
                Write("pack.json", JsonSerializer.SerializeToUtf8Bytes(new { schema_version=2, id, name=id,
                    native_payload = new { profile, registry, path_base="pack-root", reference_host_sha256=host, required_formats=formats.Values.Distinct() }, files }));
                foreach (var (name, content) in resources) Write(name, content);
                return path;
            }
            void Reject(Action action)
            {
                try { action(); } catch (InvalidDataException) { return; }
                throw new Exception("Invalid artwork/cinematic pack was accepted.");
            }
            var codec=Path.Combine(root,"authored-codec-resource");File.WriteAllText(codec,"authored identity fixture; no executable code");
            JsonObject Profile()
            {
                var p=JsonNode.Parse("{\"native\":{\"executable_sha256\":\""+host+"\",\"cinematic_path_versions\":[1],\"runtime_environment\":{\"MW34_HIRES_HUD\":\"stale\",\"MW34_HIRES_MENU\":\"stale\",\"MW34_MENU_HD_BG\":\"stale\",\"MW34_CINEMATIC_PATHS\":\"stale\"}}}")!.AsObject();
                p["native"]!["content_capabilities"] = JsonNode.Parse("{\"ui-artwork\":[1],\"cinematic-replacements\":[1]}");
                p["native"]!["runtime_environment"]!["MW34_IV50_IMAGE"]=codec;
                p["native"]!["cinematic_codec_sha256"]=Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(codec))).ToLowerInvariant();
                return p;
            }
            string Ui(string id, string kind, byte pixel=0, float u0=0)
            {
                var image = new MemoryStream();
                using (var writer = new BinaryWriter(image, Encoding.UTF8, true))
                { writer.Write("MW3H"u8); writer.Write(1); writer.Write(1); writer.Write(u0); writer.Write(0f); writer.Write(1f); writer.Write(1f); writer.Write(new byte[] {pixel,0,0,255}); }
                const string name = "ui/sprites/0123456789abcdef.rgba";
                var registry = JsonSerializer.SerializeToUtf8Bytes(new { schema_version=2, payload_profile=UiPack.Profile, kind,
                    sprites = new Dictionary<string,string> { ["0123456789abcdef"]=name }, background=(string?)null });
                return Archive(id,UiPack.Profile,UiPack.Registry,new() { [UiPack.Registry]=registry,[name]=image.ToArray() }, new() { [name]="MW3H-v1" });
            }
            var hud = manager.InstallPack(Ui("test.hud","hud"));
            var next = manager.InstallPack(Ui("test.hud2","hud",1));
            var menu = manager.InstallPack(Ui("test.menu","menu",1));
            var hudManifest = Path.Combine(hud.DirectoryPath, "pack.json");
            var originalHudManifest = File.ReadAllText(hudManifest);
            var releasedHud = JsonNode.Parse(originalHudManifest)!;
            releasedHud["native_payload"]!["reference_host_sha256"] =
                "9fd17ba2459ac2d349adda33c0c84d41772bbd2ec7c0e2a620242c696526bb83";
            File.WriteAllText(hudManifest, releasedHud.ToJsonString());
            var updatedProfile = Profile();
            updatedProfile["native"]!["executable_sha256"] =
                "dee5e15e02ae18539a3f5b7a89f1e1abac55a2afd964717c28fb900351f85f0a";
            updatedProfile["native"]!.AsObject().Remove("content_capabilities");
            UiPack.Apply(updatedProfile, new[] { hud.DirectoryPath });
            if (updatedProfile["native"]!["runtime_environment"]!["MW34_HIRES_HUD"]!.GetValue<string>() != Path.Combine(hud.DirectoryPath, "ui", "sprites"))
                throw new Exception("Published performance runtime did not activate existing HUD pack.");
            File.WriteAllText(hudManifest, originalHudManifest);
            var profile = Profile();
            UiPack.Apply(profile,new[] {hud.DirectoryPath,next.DirectoryPath});
            if (!profile["native"]!["runtime_environment"]!["MW34_HIRES_HUD"]!.GetValue<string>().StartsWith(hud.DirectoryPath)) throw new Exception("UI priority failed.");
            Reject(() => UiPack.Apply(Profile(),new[] {hud.DirectoryPath,menu.DirectoryPath}));
            var mismatch = Profile(); mismatch["native"]!["content_capabilities"] = new JsonObject();
            try
            {
                UiPack.Apply(mismatch,new[] {hud.DirectoryPath});
                throw new Exception("Mismatched UI runtime was accepted.");
            }
            catch (InvalidDataException error)
            {
                if (!error.Message.Contains(hud.Id) || !error.Message.Contains("ui-artwork") || !error.Message.Contains("version 1"))
                    throw new Exception("UI compatibility failure omitted the pack or missing capability.");
            }
            // Reproduce the installed menu revision rejected after the sky-host update.
            var menuManifestPath = Path.Combine(next.DirectoryPath, "pack.json");
            var originalMenuManifest = File.ReadAllText(menuManifestPath);
            var revisedMenuManifest = JsonNode.Parse(originalMenuManifest)!;
            revisedMenuManifest["native_payload"]!["reference_host_sha256"] = "33bfcf1d6c2b7454d6a21aee1421c34cadbc7b1be5783485b70499b5bc0e8afa";
            File.WriteAllText(menuManifestPath, revisedMenuManifest.ToJsonString());
            var skyProfile = Profile();
            skyProfile["native"]!.AsObject().Remove("content_capabilities");
            skyProfile["native"]!["executable_sha256"] = "0dec8fa9dc1671b16744b406cea2099dd5801613c037e42dbae9bd22d5fc1d93";
            UiPack.Apply(skyProfile, new[] { next.DirectoryPath });
            skyProfile["native"]!["executable_sha256"] = "d0a79be7a0e1fe30b22ca5005fa9d3c4ff133380833f80dd6d3d751766681a0d";
            UiPack.Apply(skyProfile, new[] { next.DirectoryPath });
            skyProfile["native"]!["executable_sha256"] = "b1a3edb7ed84daf399fa4bb5f3ed246a9d718470e5f6b0fac4fc16e4961af1b6";
            UiPack.Apply(skyProfile, new[] { next.DirectoryPath });
            skyProfile["native"]!["executable_sha256"] = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
            Reject(() => UiPack.Apply(skyProfile, new[] { next.DirectoryPath }));
            revisedMenuManifest["native_payload"]!.AsObject().Remove("reference_host_sha256");
            File.WriteAllText(menuManifestPath, revisedMenuManifest.ToJsonString());
            var communityProfile = Profile();
            communityProfile["native"]!["executable_sha256"] = new string('b', 64);
            UiPack.Apply(communityProfile, new[] { next.DirectoryPath });
            revisedMenuManifest["native_payload"]!["required_capabilities"] = JsonNode.Parse("{\"ui-artwork\":2}");
            File.WriteAllText(menuManifestPath, revisedMenuManifest.ToJsonString());
            Reject(() => UiPack.Apply(communityProfile, new[] { next.DirectoryPath }));
            communityProfile["native"]!["content_capabilities"]!["ui-artwork"] = new JsonArray(1, 2);
            UiPack.Apply(communityProfile, new[] { next.DirectoryPath });
            communityProfile["native"]!["content_capabilities"]!["ui-artwork"] = new JsonArray(2);
            Reject(() => UiPack.Apply(communityProfile, new[] { next.DirectoryPath }));
            File.WriteAllText(menuManifestPath, originalMenuManifest);
            Reject(() => manager.InstallPack(Ui(hud.Id,"hud",u0:float.NaN)));
            if (!File.Exists(Path.Combine(hud.DirectoryPath, UiPack.Registry))) throw new Exception("Failed update destroyed artwork.");
            UiPack.Apply(profile,Array.Empty<string>());
            var env=profile["native"]!["runtime_environment"]!.AsObject();
            if (env["MW34_HIRES_HUD"]!.GetValue<string>()!="0" || env.ContainsKey("MW34_HIRES_MENU") || env.ContainsKey("MW34_MENU_HD_BG")) throw new Exception("Disabled artwork retained hidden bindings.");
            File.WriteAllText(Path.Combine(hud.DirectoryPath,"ui/sprites/extra.rgba"),"unregistered");
            Reject(() => UiPack.Apply(Profile(),new[] {hud.DirectoryPath}));

            byte[] Avi(string handler="IV50")
            {
                byte[] Chunk(string tag, byte[] data) { using var s=new MemoryStream();using var w=new BinaryWriter(s);w.Write(Encoding.ASCII.GetBytes(tag));w.Write(data.Length);w.Write(data);if(data.Length%2!=0)w.Write((byte)0);return s.ToArray(); }
                byte[] Join(string tag, params byte[][] parts) => Encoding.ASCII.GetBytes(tag).Concat(parts.SelectMany(x=>x)).ToArray();
                var strh=new byte[56];Encoding.ASCII.GetBytes("vids"+handler).CopyTo(strh,0);BitConverter.GetBytes(1).CopyTo(strh,20);BitConverter.GetBytes(15).CopyTo(strh,24);
                var strf=new byte[40];BitConverter.GetBytes(40).CopyTo(strf,0);BitConverter.GetBytes(640).CopyTo(strf,4);BitConverter.GetBytes(480).CopyTo(strf,8);BitConverter.GetBytes((short)1).CopyTo(strf,12);BitConverter.GetBytes((short)24).CopyTo(strf,14);Encoding.ASCII.GetBytes(handler).CopyTo(strf,16);
                return Chunk("RIFF",Join("AVI ",Chunk("LIST",Join("hdrl",Chunk("LIST",Join("strl",Chunk("strh",strh),Chunk("strf",strf)))))));
            }
            string Cinema(string id,string? target,byte[] content)
            {
                var name="cinematics/media/scene"+(target==null?".mp4":".avi");
                var registry=JsonSerializer.SerializeToUtf8Bytes(new {schema_version=2,payload_profile=CinematicPack.Profile,
                    clips=new[] {new {id="scene",title="Authored fixture",source=name,replaces=target}}});
                return Archive(id,CinematicPack.Profile,CinematicPack.Registry,new() {[CinematicPack.Registry]=registry,[name]=content},new() {[name]=target==null?"MP4-library-v1":"AVI-IV50-original-v1"});
            }
            var original=Path.Combine(root,"game","Video");Directory.CreateDirectory(original);File.WriteAllBytes(Path.Combine(original,"INTRO.AVI"),Avi());
            var movie=manager.InstallPack(Cinema("test.movie","intro",Avi()));
            var second=manager.InstallPack(Cinema("test.movie2","intro",Avi()));
            var session=Path.Combine(root,"session");profile=Profile();
            CinematicPack.Apply(profile,new[]{movie.DirectoryPath,second.DirectoryPath},session,Path.GetDirectoryName(original)!);
            var map=File.ReadAllBytes(profile["native"]!["runtime_environment"]!["MW34_CINEMATIC_PATHS"]!.GetValue<string>());
            if (!map.AsSpan(0,8).SequenceEqual("MWCINE1\0"u8) || BitConverter.ToInt32(map,8)!=1 || !Encoding.UTF8.GetString(map).Contains(movie.DirectoryPath)) throw new Exception("Cinematic selection/map failed.");
            if (!File.ReadAllBytes(Path.Combine(original,"INTRO.AVI")).SequenceEqual(Avi())) throw new Exception("Cinematic selection modified original media.");
            CinematicPack.Apply(profile,Array.Empty<string>(),session,Path.GetDirectoryName(original)!);
            if (profile["native"]!["runtime_environment"]!["MW34_CINEMATIC_PATHS"]!=null) throw new Exception("Disabled movie retained replacement.");
            var absent=Profile();absent["native"]!.AsObject().Remove("cinematic_path_versions");
            Reject(()=>CinematicPack.Apply(absent,new[]{movie.DirectoryPath},session,Path.GetDirectoryName(original)!));
            var missingCodec=Profile();missingCodec["native"]!["runtime_environment"]!["MW34_IV50_IMAGE"]="missing decoder";
            Reject(()=>CinematicPack.Apply(missingCodec,Array.Empty<string>(),session,Path.GetDirectoryName(original)!));
            Reject(()=>manager.InstallPack(Cinema("test.bad","intro",Avi("H264"))));
            var unknown=manager.InstallPack(Cinema("test.unknown","new_mission_hook",Avi()));
            Reject(()=>CinematicPack.Apply(Profile(),new[]{unknown.DirectoryPath},session,Path.GetDirectoryName(original)!));
            var mp4=new byte[24];mp4[3]=24;Encoding.ASCII.GetBytes("ftypisom").CopyTo(mp4,4);
            var bonus=manager.InstallPack(Cinema("test.bonus",null,mp4));
            if(CinematicPack.Library(new[]{bonus.DirectoryPath,movie.DirectoryPath}).Single().Id!="scene") throw new Exception("Cinematic library selection failed.");
            File.AppendAllText(Path.Combine(movie.DirectoryPath,"cinematics/media/scene.avi"),"tampered");
            Reject(()=>CinematicPack.Apply(Profile(),new[]{movie.DirectoryPath},session,Path.GetDirectoryName(original)!));
            Console.WriteLine("Artwork/cinematic install, priority, disable, corruption, identity collision, runtime, trigger and format checks passed.");
        }
        finally { Directory.Delete(root,true); }
    }
}
