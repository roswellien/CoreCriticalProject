using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;
using MW3RemasterLauncher.Core;

static class ChassisPackChecks
{
    public static void Install(string archive, string output)
    {
        var manager = new PackManager(output);
        var installed = manager.InstallPack(archive);
        var rows = ChassisPack.Read(installed.DirectoryPath, installed);
        if (rows.Count == 0 || manager.InspectConflicts().Count != 0)
            throw new Exception("Additional chassis import failed.");
        Console.WriteLine("Unsigned chassis pack installed: " + installed.DirectoryPath);
    }

    public static void Run()
    {
        var root = Path.Combine(Path.GetTempPath(), "CC chassis checks " + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            var resources = new Dictionary<string, byte[]> {
                ["mesh.bin"] = "BWMESH4\0"u8.ToArray(), ["tex.bin"] = "BWTEX1\0\0"u8.ToArray(),
                ["definition.json"] = JsonSerializer.SerializeToUtf8Bytes(new {schema_version=1, template="madcat", fields=new {max_mass=75}}),
                [ChassisPack.Registry] = JsonSerializer.SerializeToUtf8Bytes(new {
                    schema_version=2, payload_profile=ChassisPack.Profile, chassis=new[] {new {
                        id="community.test:mech", name="Community Mech", controller="madcat", metadata_template="orion",
                        definition="definition.json", meshes=new {close="mesh.bin", distance="mesh.bin"},
                        textures=new {close="tex.bin", distance="tex.bin"}}}})
            };
            var files = resources.ToDictionary(p => p.Key, p => new PackFile {Bytes=p.Value.Length,
                Sha256=Convert.ToHexString(SHA256.HashData(p.Value)).ToLowerInvariant(),
                Format=p.Key=="mesh.bin"?"BWMESH4":p.Key=="tex.bin"?"BWTEX1":null});
            var manifest = new PackManifest {SchemaVersion=2, Id="community.test", Name="Community mech", Files=files,
                Provides=new PackProvides {Mechs=new(){"community.test:mech"}},
                NativePayload=new NativePackPayload {Profile=ChassisPack.Profile, Registry=ChassisPack.Registry, PathBase="pack-root",
                    RequiredFormats=new(){"BWMESH4","BWTEX1"}, RequiredCapabilities=new(){["additional-mech-chassis"]=1}}};
            var archive=Path.Combine(root,"fixture.mw3pack");
            using(var zip=ZipFile.Open(archive, ZipArchiveMode.Create))
            {
                resources["pack.json"]=JsonSerializer.SerializeToUtf8Bytes(manifest);
                foreach(var (name,bytes) in resources)
                {using var stream=zip.CreateEntry(name).Open(); stream.Write(bytes);}
            }
            var manager=new PackManager(root); var installed=manager.InstallPack(archive);
            if(ChassisPack.Read(installed.DirectoryPath,installed).Single().Id!="community.test:mech")
                throw new Exception("Chassis identity lost.");
            var old=JsonNode.Parse("""{"content_capabilities":{"prepared-mechs":[1]}}""")!.AsObject();
            try {RuntimeContentCapabilities.Require(old,installed.NativePayload!,installed.Id);throw new Exception("Old host accepted chassis.");}
            catch(InvalidDataException) {}
            var host=JsonNode.Parse("""{"content_capabilities":{"additional-mech-chassis":[1]}}""")!.AsObject();
            RuntimeContentCapabilities.Require(host,installed.NativePayload!,installed.Id);
            var icon = new byte[2066]; "MW3ICON1"u8.CopyTo(icon);
            BitConverter.GetBytes(41u).CopyTo(icon,8); BitConverter.GetBytes(50u).CopyTo(icon,12); icon[100]=255;
            var registry = JsonNode.Parse(resources[ChassisPack.Registry])!;
            registry["chassis"]![0]!["silhouette"]="icon.bin";
            registry["chassis"]![0]!["base_skin_name"]="Olive Drab";
            void SetResource(string name, byte[] bytes, string format = null)
            {
                File.WriteAllBytes(Path.Combine(installed.DirectoryPath,name),bytes);
                installed.Files![name]=new PackFile {Bytes=bytes.Length, Format=format,
                    Sha256=Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant()};
            }
            SetResource(ChassisPack.Registry,JsonSerializer.SerializeToUtf8Bytes(registry));
            SetResource("icon.bin",icon,"MW3ICON1");
            try {ChassisPack.Read(installed.DirectoryPath,installed);throw new Exception("Ungated silhouette accepted.");}
            catch(InvalidDataException) {}
            installed.NativePayload!.RequiredFormats.Add("MW3ICON1");
            installed.NativePayload.RequiredCapabilities["additional-mech-chassis"]=2;
            ChassisPack.Read(installed.DirectoryPath,installed);
            registry["chassis"]![0]!["sockets"]=JsonNode.Parse("""[{"node":"firepoint01","bone":"Forearm_Right","position":[4.0,-0.01,-1.13]}]""");
            SetResource(ChassisPack.Registry,JsonSerializer.SerializeToUtf8Bytes(registry));
            ChassisPack.Read(installed.DirectoryPath,installed);
            registry["chassis"]![0]!["sockets"]![0]!["position"]![0]=101;
            SetResource(ChassisPack.Registry,JsonSerializer.SerializeToUtf8Bytes(registry));
            try {ChassisPack.Read(installed.DirectoryPath,installed);throw new Exception("Unbounded socket accepted.");}
            catch(InvalidDataException) {}
            registry["chassis"]![0]!["sockets"]![0]!["position"]![0]=4.0;
            SetResource(ChassisPack.Registry,JsonSerializer.SerializeToUtf8Bytes(registry));
            try {RuntimeContentCapabilities.Require(host,installed.NativePayload,installed.Id);throw new Exception("Old host accepted new icon contract.");}
            catch(InvalidDataException) {}
            SetResource("icon.bin",icon[..^1],"MW3ICON1");
            try {ChassisPack.Read(installed.DirectoryPath,installed);throw new Exception("Truncated silhouette accepted.");}
            catch(InvalidDataException) {}
            SetResource("icon.bin",icon,"MW3ICON1");
            File.WriteAllBytes(Path.Combine(installed.DirectoryPath,"mesh.bin"),new byte[8]);
            try {ChassisPack.Read(installed.DirectoryPath,installed);throw new Exception("Corrupt chassis accepted.");}
            catch(InvalidDataException) {}
            Console.WriteLine("Chassis checks passed: unsigned import, stable identity, runtime capability gating, corruption rejection.");
        }
        finally {Directory.Delete(root,true);}
    }
}
