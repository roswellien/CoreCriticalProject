using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;
using MW3RemasterLauncher.Core;

static class ChassisAppearanceChecks
{
    public static void Run(PackManifest installed, JsonNode registry, Action<string, byte[], string> setResource)
    {
        // Authored 1x1 RGB565 color and its matching 1x1 BWSNR2 normal catalog.
        var color = new byte[] { 5, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 52, 18 };
        var normal = Convert.FromBase64String("QldTTlIyAAABAAAAAQAAAAEAAAABAAAAg8ixtAee7gdzdXJmYWNlMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEJXTlJNMgAAAQAAAAEAAAAAAAAAc3VyZmFjZTAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAQAAAGsRMyqti1CcgID//w==");
        var row = registry["chassis"]![0]!;
        var appearance = JsonNode.Parse("""{"upgraded":{"textures":{"example01":"upgrade.bin"},"normals":["normal.bin"]}}""")!;
        row["appearances"] = appearance;
        setResource("upgrade.bin", color, null);
        setResource("normal.bin", normal, "BWSNR2");
        void Read()
        {
            setResource(ChassisPack.Registry, JsonSerializer.SerializeToUtf8Bytes(registry), null);
            if (ChassisPack.Read(installed.DirectoryPath, installed).Single().Id != "community.test:mech")
                throw new Exception("Appearance changed chassis identity.");
        }
        void Reject()
        {
            try { Read(); }
            catch (InvalidDataException) { return; }
            throw new Exception("Invalid appearance accepted.");
        }
        Reject(); // New metadata cannot silently reach an old coordinator.
        installed.NativePayload!.RequiredCapabilities[ChassisAppearances.Capability] = 1;
        Reject(); // Normal format must be declared independently.
        installed.NativePayload.RequiredFormats.Add("BWSNR2");
        Read();
        var host = JsonNode.Parse("""{"content_capabilities":{"additional-mech-chassis":[1,2,3]}}""")!.AsObject();
        try { RuntimeContentCapabilities.Require(host, installed.NativePayload, installed.Id); throw new Exception("Old host accepted appearance feature."); }
        catch (InvalidDataException) { }
        host["content_capabilities"]![ChassisAppearances.Capability] = new JsonArray(1);
        RuntimeContentCapabilities.Require(host, installed.NativePayload, installed.Id);
        var upgraded = appearance["upgraded"]!;
        upgraded["headlights"] = new JsonArray();
        Reject();
        upgraded.AsObject().Remove("headlights");
        foreach (var path in new[] { "../upgrade.bin", "undeclared.bin" })
        {
            upgraded["textures"]!["example01"] = path;
            Reject();
        }
        upgraded["textures"]!["example01"] = "upgrade.bin";
        upgraded["textures"]!["foreign"] = "upgrade.bin";
        Reject();
        upgraded["textures"]!.AsObject().Remove("foreign");
        upgraded["normals"]!.AsArray().Add("normal.bin");
        Reject();
        upgraded["normals"]!.AsArray().RemoveAt(1);
        foreach (var invalid in new[] { normal[..^1], normal.Concat(new byte[] { 0 }).ToArray() })
        {
            setResource("normal.bin", invalid, "BWSNR2");
            Reject();
        }
        var foreign = (byte[])normal.Clone();
        foreign[24] ^= 1; // Full-content color key no longer belongs to the upgrade.
        setResource("normal.bin", foreign, "BWSNR2");
        Reject();
        var badPixels = (byte[])normal.Clone();
        badPixels[^1] ^= 1;
        setResource("normal.bin", badPixels, "BWSNR2");
        Reject();
        setResource("normal.bin", normal, "BWSNR2");
        Read();
<<<<<<< HEAD
        Console.WriteLine("Appearance checks passed: identity, feature gating, paths, inactive normal validation and full-content keys.");
=======
        var controls = new[] { "hip", "torso", "larm", "rarm", "lhand", "rhand", "lthigh", "rthigh", "lcalf", "rcalf", "lfoot", "rfoot" };
        var bones = new[] { "Pelvis", "Torso_Twist", "Upperarm_Left", "Upperarm_Right", "Forearm_Left", "Forearm_Right", "Thigh_Left", "Thigh_Right", "Calf_Left", "Calf_Right", "Foot0_Left", "Foot0_Right" };
        using var meshStream = new MemoryStream(); using var writer = new BinaryWriter(meshStream);
        void Name(string name) { writer.Write(System.Text.Encoding.ASCII.GetBytes(name.PadRight(32, '\0'))); }
        void Matrix() { for (var i = 0; i < 16; ++i) writer.Write(i % 5 == 0 ? 1.0 : 0.0); }
        writer.Write("BWMESH4\0"u8.ToArray());
        foreach (var number in new uint[] { 1, 12, 12, 0 }) writer.Write(number);
        for (var i = 0; i < 5; ++i) writer.Write(0.0);
        for (var i = 0; i < 12; ++i) { Name(bones[i]); Name(controls[i]); writer.Write(i == 0 ? -1 : 0); Matrix(); }
        foreach (var control in controls) { Name(control); Matrix(); }
        Name("hip"); Name("hip"); writer.Write(0u); writer.Write(3u); writer.Write(0xffffffffu);
        for (var i = 0; i < 3; ++i) foreach (var value in new float[] { 0, 0, 0, 0, 0, 1, 0, 0 }) writer.Write(value);
        var mesh = meshStream.ToArray();
        using var textureStream = new MemoryStream(); using var textureWriter = new BinaryWriter(textureStream);
        textureWriter.Write("BWTEX1\0\0"u8.ToArray());
        foreach (var number in new uint[] { 1, 1, 0 }) textureWriter.Write(number);
        textureWriter.Write(System.Text.Encoding.ASCII.GetBytes("paint".PadRight(32, '\0')));
        textureWriter.Write(1u); textureWriter.Write(1u); textureWriter.Write(0ul); textureWriter.Write((ushort)0x1234);
        var texture = textureStream.ToArray();
        setResource("owned.mesh", mesh, "BWMESH4"); setResource("owned.texture", texture, "BWTEX1");
        appearance["new"] = JsonNode.Parse("""{"schema_version":1,"meshes":{"close":"owned.mesh","distance":"owned.mesh"},"textures":{"close":"owned.texture","distance":"owned.texture"},"normals":["normal.bin"]}""");
        Reject(); // New geometry formats must be declared even when inactive.
        installed.NativePayload.RequiredFormats.Insert(1, "BWMESH4");
        installed.NativePayload.RequiredFormats.Insert(2, "BWTEX1");
        Read();
        var sourceJoints = (byte[])mesh.Clone();
        BitConverter.GetBytes(2u).CopyTo(sourceJoints, 20);
        setResource("owned.mesh", sourceJoints, "BWMESH4"); Read();
        var armRest = (byte[])mesh.Clone();
        BitConverter.GetBytes(3u).CopyTo(armRest, 20);
        var parents = new[] { -1, 0, 1, 1, 2, 3, 0, 0, 6, 7, 8, 9 };
        for (var i = 0; i < parents.Length; ++i) BitConverter.GetBytes(parents[i]).CopyTo(armRest, 128 + i * 196);
        setResource("owned.mesh", armRest, "BWMESH4"); Read();
        foreach (var (offset, bytes) in new[] {
            (128 + 2 * 196, BitConverter.GetBytes(0)),
            (128 + 4 * 196, BitConverter.GetBytes(3)),
            (64 + 4 * 196 + 32, System.Text.Encoding.ASCII.GetBytes("rhand".PadRight(32, '\0'))),
            (64 + 2 * 196, System.Text.Encoding.ASCII.GetBytes("Foreign".PadRight(32, '\0'))),
            (128 + 6 * 196, BitConverter.GetBytes(4)),
            (64 + 2 * 196 + 68, BitConverter.GetBytes(0.0)) })
        {
            var invalid = (byte[])armRest.Clone(); bytes.CopyTo(invalid, offset);
            setResource("owned.mesh", invalid, "BWMESH4"); Reject();
        }
        BitConverter.GetBytes(4u).CopyTo(sourceJoints, 20);
        setResource("owned.mesh", sourceJoints, "BWMESH4"); Reject();
        foreach (var invalid in new[] { mesh[..^1], mesh.Concat(new byte[] { 0 }).ToArray() })
        { setResource("owned.mesh", invalid, "BWMESH4"); Reject(); }
        setResource("owned.mesh", mesh, "BWMESH4");
        appearance["new"]!["textures"]!.AsObject().Remove("distance"); Reject();
        appearance["new"]!["textures"]!["distance"] = "owned.texture";
        setResource("owned.texture", texture[..^1], "BWTEX1"); Reject();
        setResource("owned.texture", texture, "BWTEX1");
        Read();
        var ownedValue = appearance["new"]!.DeepClone();
        foreach (var malformed in new[] { "null", "1", "true", "[]", "\"bad\"" })
        { appearance["new"] = JsonNode.Parse(malformed); Reject(); }
        appearance["new"] = ownedValue;
        foreach (var malformed in new[] { "true", "\"1\"" })
        { appearance["new"]!["schema_version"] = JsonNode.Parse(malformed); Reject(); }
        appearance["new"]!["schema_version"] = 1;
        appearance["new"]!["meshes"]!["normals"] = "owned.mesh"; Reject();
        appearance["new"]!["meshes"]!.AsObject().Remove("normals");
        var singular = (byte[])mesh.Clone();
        Array.Clear(singular, 64 + 68, 8); // First rest matrix loses its X basis.
        setResource("owned.mesh", singular, "BWMESH4"); Reject();
        setResource("owned.mesh", mesh, "BWMESH4");
        var badName = (byte[])texture.Clone(); badName[20] = (byte)'/';
        setResource("owned.texture", badName, "BWTEX1"); Reject();
        setResource("owned.texture", texture, "BWTEX1"); Read();
        // This descriptor was serialized by the independent Python writer from
        // the authored mesh/color fixture above, not by this C# reader.
        var emission = Convert.FromBase64String("QldNRU0xAAABAAAA1k4tpZXLBDRleWVzAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABoaXAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHBhaW50AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAAEAAACDyLG0B57uBzMzsz4BAAAAAgAAAAAAAADNzEw+mpmZPjMzMz9sZWZ0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJqZmb4AAAAAzcxMPgAAgD8K1yM8CtcjPJqZmT/NzMw9cmlnaHQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACamZk+AAAAAM3MTD4AAIA/CtcjPArXIzyamZk/zczMPQ==");
        setResource("owned.emission", emission, "BWMEM1");
        appearance["new"]!["emission"] = JsonNode.Parse("""{"close":"owned.emission","distance":"owned.emission"}""");
        Reject(); // A new payload cannot omit its declared format.
        installed.NativePayload.RequiredFormats.Add("BWMEM1");
        Read();
        foreach (var offset in new[] { 0, 12, 52, 56, 120, 128 })
        {
            var corrupt = (byte[])emission.Clone(); corrupt[offset] ^= 1;
            setResource("owned.emission", corrupt, "BWMEM1"); Reject();
        }
        foreach (var corrupt in new[] { emission[..^1], emission.Concat(new byte[] { 0 }).ToArray() })
        { setResource("owned.emission", corrupt, "BWMEM1"); Reject(); }
        var badStrength = (byte[])emission.Clone(); BitConverter.GetBytes(float.NaN).CopyTo(badStrength, 136);
        setResource("owned.emission", badStrength, "BWMEM1"); Reject();
        var badAnchor = (byte[])emission.Clone(); BitConverter.GetBytes(8f).CopyTo(badAnchor, 196);
        setResource("owned.emission", badAnchor, "BWMEM1"); Reject();
        setResource("owned.emission", emission, "BWMEM1"); Read();
        var weightedMesh = mesh.Concat(new byte[12]).ToArray();
        BitConverter.GetBytes(uint.MaxValue).CopyTo(weightedMesh, 64 + 12 * 196 + 12 * 160 + 64);
        setResource("owned.mesh", weightedMesh, "BWMESH4"); Reject();
        setResource("owned.mesh", mesh, "BWMESH4"); Read();
        appearance["new"]!["emission"]!.AsObject().Remove("distance"); Reject();
        appearance["new"]!["emission"]!["distance"] = "owned.emission"; Read();
        // Retain the authored vertex stream, but rigidly bind it to the left
        // forearm. The independently authored emission fixture pins its hash.
        var weaponMesh = (byte[])mesh.Clone();
        BitConverter.GetBytes(4u).CopyTo(weaponMesh, 64 + 12 * 196 + 12 * 160 + 64);
        setResource("owned.mesh", weaponMesh, "BWMESH4");
        var attachment = JsonNode.Parse("""{"schema_version":1,"close":{"mesh_identity":"3404cb95a52d4ed6","records":[{"source_control":"lhand","weapon":"ERLargeLaser","bone":"Forearm_Left","position":[0,0,0]}]},"distance":{"mesh_identity":"3404cb95a52d4ed6","records":[{"source_control":"lhand","weapon":"ERLargeLaser","bone":"Forearm_Left","position":[0,0,0]}]}}""")!;
        appearance["new"]!["weapon_attachments"] = attachment;
        Read();
        attachment["close"]!["mesh_identity"] = "0000000000000000"; Reject();
        attachment["close"]!["mesh_identity"] = "3404cb95a52d4ed6";
        attachment["close"]!["records"]![0]!["position"]![0] = 2; Reject();
        attachment["close"]!["records"]![0]!["position"]![0] = 0;
        attachment["close"]!["records"]!.AsArray().Add(attachment["close"]!["records"]![0]!.DeepClone()); Reject();
        attachment["close"]!["records"]!.AsArray().RemoveAt(1);
        attachment["distance"]!["records"]![0]!["weapon"] = "OtherLaser"; Reject();
        attachment["distance"]!["records"]![0]!["weapon"] = "ERLargeLaser"; Read();
        appearance["new"]!.AsObject().Remove("weapon_attachments");
        setResource("owned.mesh", mesh, "BWMESH4"); Read();
        Console.WriteLine("Appearance checks passed: identity, feature gating, paths, normal validation and authored emission integrity.");
>>>>>>> origin/develop
    }
}
