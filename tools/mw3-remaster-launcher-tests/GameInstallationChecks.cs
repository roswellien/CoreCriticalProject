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
    private static void ExpectFailure(Action action)
    {
        try { action(); }
        catch (Exception error) when (error is IOException or InvalidDataException) { return; }
        throw new Exception("Invalid installation unexpectedly succeeded.");
    }
}
