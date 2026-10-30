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
        Console.WriteLine("Appearance checks passed: identity, feature gating, paths, inactive normal validation and full-content keys.");
    }
}
