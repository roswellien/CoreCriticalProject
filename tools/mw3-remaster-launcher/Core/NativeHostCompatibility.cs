namespace MW3RemasterLauncher.Core;

/// <summary>Exact successors reviewed for unchanged artwork/movie resource readers.</summary>
public static class NativeHostCompatibility
{
    public static bool Matches(string reference, string actual) =>
        string.Equals(reference, actual, StringComparison.OrdinalIgnoreCase) ||
        (string.Equals(reference, "9fd17ba2459ac2d349adda33c0c84d41772bbd2ec7c0e2a620242c696526bb83", StringComparison.OrdinalIgnoreCase) &&
         new[] {
             "c1afedadd8ed9e13a956db917a1a5335a6581fac01374b367969d4e985852115",
             "a99afd84ddb8fb2375197d0406186286ce8d8775399cbf75373c5a07bcd8482c",
             // Current feature branch + audited readability files + explicit user support paths.
             // UI and movie resource readers are byte-identical to their admitted predecessors.
             "8194028a835c85e46b0963864ea04acfe400749671b1eb7f28ae63a51a2f5532",
             "9c578de615168724fb40664ad03b870b34b68169802cd0fae371a6f2c2d666b6", // Sky backdrop classification; resource readers unchanged.
             "0dec8fa9dc1671b16744b406cea2099dd5801613c037e42dbae9bd22d5fc1d93",
             "d0a79be7a0e1fe30b22ca5005fa9d3c4ff133380833f80dd6d3d751766681a0d",
             "b1a3edb7ed84daf399fa4bb5f3ed246a9d718470e5f6b0fac4fc16e4961af1b6", // Positive-depth untextured lower horizon; readers unchanged. // Terrain keeps normal rendering at the sky depth threshold. // Sky backdrop classification; resource readers unchanged.
             // Same seven authored objects and exact regenerated translations,
             // linked as the host plus the player's native module.
             "e293b3a5f79d3d85f7c04ddcd9f857046e66583f6c7d18255e3ceb43c2cfc46c",
             "c922df9f8663315972d14376ab5ac622cf82316d8ecf78a9c5eda7ecdca9ae95" // Rebuilt lower-horizon split host; readers unchanged.
         }.Contains(actual, StringComparer.OrdinalIgnoreCase)) ||
        // Cinematic-pack reference uses byte-identical gpu_hud.inc and vdd.inc readers.
        (string.Equals(reference, "33bfcf1d6c2b7454d6a21aee1421c34cadbc7b1be5783485b70499b5bc0e8afa", StringComparison.OrdinalIgnoreCase) &&
         (string.Equals(actual, "0dec8fa9dc1671b16744b406cea2099dd5801613c037e42dbae9bd22d5fc1d93", StringComparison.OrdinalIgnoreCase) ||
          (string.Equals(actual, "d0a79be7a0e1fe30b22ca5005fa9d3c4ff133380833f80dd6d3d751766681a0d", StringComparison.OrdinalIgnoreCase) ||
           string.Equals(actual, "b1a3edb7ed84daf399fa4bb5f3ed246a9d718470e5f6b0fac4fc16e4961af1b6", StringComparison.OrdinalIgnoreCase) ||
           string.Equals(actual, "c922df9f8663315972d14376ab5ac622cf82316d8ecf78a9c5eda7ecdca9ae95", StringComparison.OrdinalIgnoreCase))));
}
