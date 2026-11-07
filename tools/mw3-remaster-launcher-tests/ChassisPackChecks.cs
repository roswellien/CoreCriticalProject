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
        LegacyChassisSkinChecks.Run();
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
            var hingeHeader = new byte[24];
            "BWMESH4\0"u8.CopyTo(hingeHeader);
            BitConverter.GetBytes(3u).CopyTo(hingeHeader,20);
            var meshName = "mesh.bin";
            File.WriteAllBytes(Path.Combine(installed.DirectoryPath,meshName),hingeHeader);
            installed.Files![meshName] = new PackFile {Bytes=hingeHeader.Length,
                Sha256=Convert.ToHexString(SHA256.HashData(hingeHeader)).ToLowerInvariant(),Format="BWMESH4"};
            try {ChassisPack.Read(installed.DirectoryPath,installed);throw new Exception("Ungated hinge rig accepted.");}
            catch(InvalidDataException) {}
            installed.NativePayload!.RequiredCapabilities["donor-rig-hinges"]=1;
            ChassisPack.Read(installed.DirectoryPath,installed);
            try {RuntimeContentCapabilities.Require(host,installed.NativePayload,installed.Id);throw new Exception("Old host accepted hinge rig.");}
            catch(InvalidDataException) {}
            host["content_capabilities"]!["donor-rig-hinges"]=new JsonArray(1);
            RuntimeContentCapabilities.Require(host,installed.NativePayload,installed.Id);
            File.WriteAllBytes(Path.Combine(installed.DirectoryPath,meshName),resources[meshName]);
            installed.Files[meshName] = files[meshName] = new PackFile {Bytes=resources[meshName].Length,
                Sha256=Convert.ToHexString(SHA256.HashData(resources[meshName])).ToLowerInvariant(),Format="BWMESH4"};
            installed.NativePayload.RequiredCapabilities.Remove("donor-rig-hinges");
            var headlightRegistry=JsonNode.Parse(resources[ChassisPack.Registry])!;
            var light=JsonNode.Parse("""{"id":"left","space":"guest_node","attachment":"torso","position":[1,2,3],"direction":[0,0,-1],"color":[1,1,1],"intensity":2,"range":50,"inner_angle":15,"outer_angle":30}""")!;
            headlightRegistry["chassis"]![0]!["headlights"]=new JsonArray(light);
            void PutLights()
            {
                var bytes=JsonSerializer.SerializeToUtf8Bytes(headlightRegistry);
                File.WriteAllBytes(Path.Combine(installed.DirectoryPath,ChassisPack.Registry),bytes);
                installed.Files![ChassisPack.Registry]=new PackFile {Bytes=bytes.Length,Sha256=Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant()};
            }
            PutLights();
            try{ChassisPack.Read(installed.DirectoryPath,installed);throw new Exception("Ungated headlights accepted");}catch(InvalidDataException){}
            installed.NativePayload!.RequiredCapabilities["additional-mech-chassis"]=2;
            installed.NativePayload.RequiredCapabilities["mech-headlights"]=1;
            ChassisPack.Read(installed.DirectoryPath,installed);
            foreach(var invalid in new JsonNode[]{JsonValue.Create(true)!,JsonValue.Create(-1)!,JsonValue.Create(257)!})
            {
                light["range"]=invalid.DeepClone();PutLights();
                try{ChassisPack.Read(installed.DirectoryPath,installed);throw new Exception("Invalid lamp accepted");}catch(InvalidDataException){}
            }
            installed.NativePayload.RequiredCapabilities.Remove("mech-headlights");
            installed.NativePayload.RequiredCapabilities["additional-mech-chassis"]=1;
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
            var sfm = new byte[36]; "BWSFM1\0\0"u8.CopyTo(sfm);
            BitConverter.GetBytes(1u).CopyTo(sfm,8); BitConverter.GetBytes(1u).CopyTo(sfm,12);
            BitConverter.GetBytes(0xffffffffu).CopyTo(sfm,32);
            registry["chassis"]![0]!["surface_materials"]=JsonNode.Parse("""{"close":"sfm.bin","distance":"sfm.bin"}""");
            SetResource(ChassisPack.Registry,JsonSerializer.SerializeToUtf8Bytes(registry));
            SetResource("sfm.bin",sfm,"BWSFM1");
            try {ChassisPack.Read(installed.DirectoryPath,installed);throw new Exception("Ungated surface_materials accepted.");}
            catch(InvalidDataException) {}
            installed.NativePayload.RequiredFormats.Add("BWSFM1");
            installed.NativePayload.RequiredCapabilities["surface-materials"]=1;
            ChassisPack.Read(installed.DirectoryPath,installed);
            var builderBoundary = (byte[])sfm.Clone();
            BitConverter.GetBytes(65u).CopyTo(builderBoundary,20);
            SetResource("sfm.bin",builderBoundary,"BWSFM1");
            ChassisPack.Read(installed.DirectoryPath,installed);
            var hostWithIconOnly=JsonNode.Parse("""{"content_capabilities":{"additional-mech-chassis":[1,2]}}""")!.AsObject();
            try {RuntimeContentCapabilities.Require(hostWithIconOnly,installed.NativePayload,installed.Id);throw new Exception("Old host accepted surface-materials pack.");}
            catch(InvalidDataException) {}
            var hostWithSurface=JsonNode.Parse("""{"content_capabilities":{"additional-mech-chassis":[1,2],"surface-materials":[1]}}""")!.AsObject();
            RuntimeContentCapabilities.Require(hostWithSurface,installed.NativePayload,installed.Id);
            SetResource("sfm.bin",sfm[..35],"BWSFM1");
            try {ChassisPack.Read(installed.DirectoryPath,installed);throw new Exception("Truncated BWSFM1 accepted.");}
            catch(InvalidDataException) {}
            SetResource("sfm.bin",sfm,"BWSFM1");
            File.WriteAllBytes(Path.Combine(installed.DirectoryPath,"mesh.bin"),new byte[8]);
            try {ChassisPack.Read(installed.DirectoryPath,installed);throw new Exception("Corrupt chassis accepted.");}
            catch(InvalidDataException) {}

            // Import checks pin and bound every legacy reference. The coordinator
            // separately validates the binary model/motion formats before launch.
            installed.Files!.Clear();
            var legacyDescriptor = JsonNode.Parse("""
                {"schema_version":1,"resource":"example","definition":"raw.bin",
                 "materials":"raw.bin","silhouette":"raw.bin",
                 "models":{"close":"raw.bin","distance":"raw.bin","cockpit":"raw.bin"},
                 "motions":{"example_walk":"raw.bin"},"animations":{"anim_example.zrd":"raw.bin"},
                 "textures":{"example01":"raw.bin"}}
                """)!;
            var legacyRegistry = JsonNode.Parse("""
                {"schema_version":2,"payload_profile":"additional-chassis-v1","chassis":[
                  {"id":"community.test:mech","name":"Example","metadata_template":"annihilator","legacy":"legacy.json"}]}
                """)!;
            SetResource("raw.bin",new byte[]{1});
            SetResource("legacy.json",JsonSerializer.SerializeToUtf8Bytes(legacyDescriptor));
            SetResource(ChassisPack.Registry,JsonSerializer.SerializeToUtf8Bytes(legacyRegistry));
            installed.NativePayload.RequiredFormats=new(){"MW3LEGACY"};
            try {ChassisPack.Read(installed.DirectoryPath,installed);throw new Exception("Legacy data accepted without version 3.");}
            catch(InvalidDataException) {}
            installed.NativePayload.RequiredCapabilities["additional-mech-chassis"]=3;
            ChassisPack.Read(installed.DirectoryPath,installed);
            try {RuntimeContentCapabilities.Require(host,installed.NativePayload,installed.Id);throw new Exception("Old host accepted legacy chassis.");}
            catch(InvalidDataException) {}
            foreach (var invalid in new[]{"undeclared.bin","../raw.bin"})
            {
                legacyDescriptor["motions"]!["example_walk"]=invalid;
                SetResource("legacy.json",JsonSerializer.SerializeToUtf8Bytes(legacyDescriptor));
                try {ChassisPack.Read(installed.DirectoryPath,installed);throw new Exception("Unpinned legacy reference accepted.");}
                catch(InvalidDataException) {}
            }
            Console.WriteLine("Chassis checks passed: unsigned import, stable identity, runtime capability gating, corruption rejection.");
        }
        finally {Directory.Delete(root,true);}
    }
}
