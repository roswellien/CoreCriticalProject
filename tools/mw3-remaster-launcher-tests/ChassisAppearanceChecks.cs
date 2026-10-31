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
        Console.WriteLine("Appearance checks passed: identity, feature gating, paths, inactive normal validation and full-content keys.");
    }
}
