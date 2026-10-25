namespace MW3RemasterLauncher.Core;

/// <summary>A validated graphics selection shared by setup and normal launch.</summary>
public sealed record GraphicsPreferences(int Width, int Height, string WindowMode,
    string AntiAliasing, int AnisotropicFiltering, int DrawDistance, int FogDistance,
    bool DynamicLighting, bool Shadows)
{
    public static GraphicsPreferences From(LauncherSettings s) => new(s.Width, s.Height,
        s.WindowMode, s.AntiAliasing, s.AnisotropicFiltering, s.DrawDistance, s.FogDistance,
        s.DynamicLighting, s.Shadows);

    public void Validate()
    {
        if (Width < 640 || Height < 480 || Width > 7680 || Height > 4320)
            throw new InvalidOperationException("Choose a supported display resolution.");
        if (WindowMode is not ("fullscreen_windowed" or "fullscreen" or "windowed"))
            throw new InvalidOperationException("Choose a supported window mode.");
        if (AntiAliasing is not ("off" or "1" or "fxaa" or "2" or "4"))
            throw new InvalidOperationException("Choose a supported AA setting.");
        if (AnisotropicFiltering is not (1 or 2 or 4 or 8 or 16))
            throw new InvalidOperationException("Choose a supported AF setting.");
        if (DrawDistance is not (800 or 1200 or 1600 or 2400 or 3200) || FogDistance is not (0 or 1100))
            throw new InvalidOperationException("Choose supported scenery and fog settings.");
    }

    public void ApplyTo(LauncherSettings s)
    {
        Validate();
        s.Width=Width; s.Height=Height; s.WindowMode=WindowMode;
        s.Fullscreen=WindowMode!="windowed";
        s.AntiAliasing=AntiAliasing; s.AnisotropicFiltering=AnisotropicFiltering;
        s.DrawDistance=DrawDistance; s.FogDistance=FogDistance;
        s.DynamicLighting=DynamicLighting; s.Shadows=Shadows;
    }
}
