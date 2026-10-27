using System.IO;
using System.Security.Cryptography;
using System.Buffers.Binary;
using MW3RemasterLauncher.Core;

static class GameInstallationChecks
{
    public static void Run()
    {
        var root = Path.Combine(Path.GetTempPath(), "mw3-install-check-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        try
        {
            // Authored PE fixture: signing changes metadata and appends a certificate,
            // but every byte of the executable payload must retain its pinned identity.
            var unsigned = new byte[512]; unsigned[0] = (byte)'M'; unsigned[1] = (byte)'Z';
            BinaryPrimitives.WriteInt32LittleEndian(unsigned.AsSpan(60), 64);
            BinaryPrimitives.WriteUInt32LittleEndian(unsigned.AsSpan(64), 0x4550);
            BinaryPrimitives.WriteUInt16LittleEndian(unsigned.AsSpan(88), 0x20b);
            unsigned[400] = 73;
            var unsignedHash = Convert.ToHexString(SHA256.HashData(unsigned));
            var signed = new byte[528]; unsigned.CopyTo(signed, 0);
            BinaryPrimitives.WriteUInt32LittleEndian(signed.AsSpan(152), 12345);
            BinaryPrimitives.WriteUInt32LittleEndian(signed.AsSpan(232), 512);
            BinaryPrimitives.WriteUInt32LittleEndian(signed.AsSpan(236), 16);
            BinaryPrimitives.WriteUInt32LittleEndian(signed.AsSpan(512), 16);
            BinaryPrimitives.WriteUInt16LittleEndian(signed.AsSpan(516), 0x200);
            BinaryPrimitives.WriteUInt16LittleEndian(signed.AsSpan(518), 2);
            if (!PinnedPeImage.MatchesSignedImage(signed, 512, unsignedHash))
                throw new Exception("Certificate-only attachment changed pinned extractor admission.");
            var changed = (byte[])signed.Clone(); changed[400] ^= 1;
            if (PinnedPeImage.MatchesSignedImage(changed, 512, unsignedHash) ||
                PinnedPeImage.MatchesSignedImage(signed[..^1], 512, unsignedHash) ||
                PinnedPeImage.MatchesSignedImage(signed.Concat(new byte[8]).ToArray(), 512, unsignedHash))
                throw new Exception("Changed code, truncated certificate or appended data passed extractor admission.");
            changed = (byte[])signed.Clone(); changed[232] = 8;
            if (PinnedPeImage.MatchesSignedImage(changed, 512, unsignedHash))
                throw new Exception("An overlapping certificate table passed extractor admission.");
            changed = (byte[])signed.Clone(); changed[518] = 1;
            if (PinnedPeImage.MatchesSignedImage(changed, 512, unsignedHash))
                throw new Exception("A malformed certificate record passed extractor admission.");
            var fixture = Path.Combine(root, "authored.txt");
            PackStorage.Resolve(Path.GetPathRoot(root)!, "MW3CD.TXT");
            File.WriteAllText(fixture, "authored installation fixture");
            var hash = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(fixture)));
            GameInstallation.VerifyFile(fixture, hash);
            ExpectFailure(() => GameInstallation.VerifyFile(fixture, new string('0', 64)));
            ExpectFailure(() => GameInstallation.VerifyFile(fixture, hash, 1));
            ExpectFailure(() => GameInstallation.VerifyExistingAsync(root).GetAwaiter().GetResult());
            CheckOptionalTiers(root);
            // An existing destination is protected even if source, patch and tools are invalid.
            var destination = Path.Combine(root, "game");
            Directory.CreateDirectory(destination);
            var sentinel = Path.Combine(destination, "save.dat");
            File.WriteAllText(sentinel, "keep this save");
            ExpectFailure(() => GameInstallation.InstallDirectoryAsync(root, fixture, destination, root).GetAwaiter().GetResult());
            if (File.ReadAllText(sentinel) != "keep this save") throw new Exception("Existing game data was modified.");
            // Failed staging never publishes a destination or leaves a partial installation.
            File.WriteAllText(Path.Combine(root, "unshield.exe"), "authored unknown extractor; must never execute");
            var failed = Path.Combine(root, "new-game");
            ExpectFailure(() => GameInstallation.InstallDirectoryAsync(root, fixture, failed, root).GetAwaiter().GetResult());
            if (Directory.Exists(failed) || Directory.GetDirectories(root, ".mw3-install-*").Length != 0)
                throw new Exception("Failed install left a published/partial game directory.");
            Console.WriteLine("Original-data setup checks passed.");
        }
        finally { Directory.Delete(root, true); }
    }
    private static void CheckOptionalTiers(string root)
    {
        // The supported closure names every required file, and no tier the runtime can do without.
        var empty = Path.Combine(root, "empty-install");
        Directory.CreateDirectory(empty);
        var closure = ExpectMissing(() => GameInstallation.VerifyExistingAsync(empty).GetAwaiter().GetResult());
        foreach (var required in new[] { "Mech3.exe", "zbd/c1/gamez.zbd", "zbd/c1/rtexture.zbd", "zbd/t1/rtexture2.zbd",
            "zbd/c4b/rtexture3.zbd", "zbd/rmechtex.zbd", "zbd/rmechtex16.zbd", "zbd/soundsH.zbd or zbd/soundsL.zbd" })
            if (!closure.Contains(required + ",") && !closure.EndsWith(required))
                throw new Exception("A required original file was not reported missing: " + required);
        foreach (var optional in new[] { "/texture.zbd", "/texture1.zbd", "/texture2.zbd", "rmechtexs.zbd" })
            if (closure.Contains(optional)) throw new Exception("An unused texture tier was required: " + optional);

        // Authored retail layout: no medium software textures and no low-fidelity sound bank.
        var install = Path.Combine(root, "retail-install");
        GameInstallation.ContentFile Authored(string source, string target, bool write = true)
        {
            var bytes = System.Text.Encoding.UTF8.GetBytes("authored " + source + "/" + target);
            if (write)
            {
                var path = PackStorage.Resolve(install, target);
                Directory.CreateDirectory(Path.GetDirectoryName(path)!);
                File.WriteAllBytes(path, bytes);
            }
            return new(source + "/" + target, target, bytes.Length, Convert.ToHexString(SHA256.HashData(bytes)));
        }
        var gamez = Authored("Database_Files", "zbd/c1/gamez.zbd");
        var reader = Authored("Database_Files", "zbd/c1/reader.zbd");
        var hardware = Authored("Hardware_Texture_8", "zbd/c1/rtexture.zbd");
        var best = Authored("Software_Texture_Best", "zbd/c1/texture.zbd");
        var medium = Authored("Software_Texture_Medium", "zbd/c1/texture2.zbd", false);
        var high = Authored("Sound_High_Fidelity", "zbd/soundsH.zbd");
        var low = Authored("Sound_Low_Fidelity", "zbd/soundsL.zbd", false);
        var patchedReader = Authored("Patch_Files", "zbd/c1/reader.zbd");
        GameInstallation.ContentFile[] baseFiles = [gamez, reader, hardware, best, medium, high, low];
        GameInstallation.ContentFile[] patchFiles = [patchedReader];
        void Verify() => GameInstallation.VerifyExistingAsync(install, baseFiles, patchFiles).GetAwaiter().GetResult();
        Verify();

        // Present optional files are still identity-checked.
        File.WriteAllText(PackStorage.Resolve(install, best.Target), "damaged");
        ExpectFailure(Verify);
        File.Delete(PackStorage.Resolve(install, best.Target));
        Verify();

        // Every missing required file is reported, and at least one sound bank must remain.
        File.Delete(PackStorage.Resolve(install, gamez.Target));
        File.Delete(PackStorage.Resolve(install, hardware.Target));
        File.Delete(PackStorage.Resolve(install, high.Target));
        var message = ExpectMissing(Verify);
        if (message != "3 required installation files are missing: zbd/c1/gamez.zbd, zbd/c1/rtexture.zbd, " +
            "zbd/soundsH.zbd or zbd/soundsL.zbd")
            throw new Exception("Missing installation files were not all reported: " + message);
    }
    private static string ExpectMissing(Action action)
    {
        try { action(); }
        catch (FileNotFoundException error) { return error.Message; }
        throw new Exception("An incomplete installation unexpectedly passed.");
    }
    private static void ExpectFailure(Action action)
    {
        try { action(); }
        catch (Exception error) when (error is IOException or InvalidDataException) { return; }
        throw new Exception("Invalid installation unexpectedly succeeded.");
    }
}
