using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;
using MW3RemasterLauncher.Core;

static class SkinPackChecks
{
    public static void Install(string archive, string output)
    {
        var manager = new PackManager(output);
        var installed = manager.InstallPack(archive);
        var skins = SkinPack.Read(installed.DirectoryPath, installed);
        if (skins.Count != 1 || skins[0].Name != "Sommerset" || installed.Provides?.Mechs?.Count > 0)
            throw new Exception("Sommerset installation did not preserve additive identity.");
        Console.WriteLine("Unsigned Sommerset asset pack installed and verified: " + installed.DirectoryPath);
    }

    public static void Run()
    {
        var root = Path.Combine(Path.GetTempPath(), "CC skin checks " + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            var content = "BWTEX1\0\0"u8.ToArray();
            var registry = JsonSerializer.SerializeToUtf8Bytes(new {
                schema_version=2, payload_profile=SkinPack.Profile, skins=new[] { new {
                    id="test.skin:sommerset", name="Sommerset", chassis="bushwacker",
                    mesh_sha256=new { close=new string('a',64), distance=new string('b',64) },
                    textures=new { close="payload.bin", distance="payload.bin" } } } });
            var files = new Dictionary<string, PackFile>();
            foreach(var (name,bytes) in new[] { (SkinPack.Registry,registry), ("payload.bin",content) })
                files[name]=new PackFile { Bytes=bytes.Length, Sha256=Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant(),
                    Format=name.EndsWith(".bin")?"BWTEX1":null };
            var manifest = new PackManifest { SchemaVersion=2, Id="test.skin", Name="Sommerset", Provides=new PackProvides { Textures=true }, Files=files,
                NativePayload=new NativePackPayload { Profile=SkinPack.Profile,Registry=SkinPack.Registry,PathBase="pack-root",RequiredFormats=new(){"BWTEX1"},
                    RequiredCapabilities=new(){["additional-mech-skins"]=1} } };
            var archive=Path.Combine(root,"fixture.mw3pack");
            using(var zip=ZipFile.Open(archive,ZipArchiveMode.Create))
                foreach(var (name,bytes) in new[] { ("pack.json",JsonSerializer.SerializeToUtf8Bytes(manifest)), (SkinPack.Registry,registry), ("payload.bin",content) })
                { using var stream=zip.CreateEntry(name).Open();stream.Write(bytes); }
            var manager=new PackManager(root);var installed=manager.InstallPack(archive);
            if(SkinPack.Read(installed.DirectoryPath,installed).Single().Id!="test.skin:sommerset" || manager.InspectConflicts().Count!=0)
                throw new Exception("Added skin was treated as a chassis replacement.");
            var oldHost=JsonNode.Parse("""{"content_capabilities":{"prepared-mechs":[1]}}""")!.AsObject();
            try { RuntimeContentCapabilities.Require(oldHost,installed.NativePayload!,installed.Id);throw new Exception("Old host accepted skin capability."); }
            catch(InvalidDataException) { }
            var host=JsonNode.Parse("""{"content_capabilities":{"additional-mech-skins":[1]}}""")!.AsObject();
            RuntimeContentCapabilities.Require(host,installed.NativePayload!,installed.Id);
            File.WriteAllBytes(Path.Combine(installed.DirectoryPath,"payload.bin"),new byte[8]);
            try { SkinPack.Read(installed.DirectoryPath,installed);throw new Exception("Corrupt skin accepted."); }
            catch(InvalidDataException) { }
            Console.WriteLine("Skin pack checks passed: unsigned import, named identity, no chassis conflict, capability rejection and corrupt payload.");
        }
        finally { Directory.Delete(root,true); }
    }
}
