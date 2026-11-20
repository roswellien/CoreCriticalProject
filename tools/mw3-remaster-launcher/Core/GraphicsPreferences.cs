namespace MW3RemasterLauncher.Core;

/// <summary>A validated graphics selection shared by setup and normal launch.</summary>
public sealed record GraphicsPreferences(int Width, int Height, string WindowMode,
    string AntiAliasing, int AnisotropicFiltering, int DrawDistance,
    bool DynamicLighting, bool Shadows, bool Headlights = false,
    bool WaterDetail = true, bool CloudDetail = true, string FlareStyle = "modern")
{
    public static GraphicsPreferences From(LauncherSettings s) => new(s.Width, s.Height,
        s.WindowMode, s.AntiAliasing, s.AnisotropicFiltering, s.DrawDistance,
        s.DynamicLighting, s.Shadows, s.Headlights, s.WaterDetail, s.CloudDetail, s.FlareStyle);

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
        if (DrawDistance is not (800 or 1200 or 1600 or 2400 or 3200))
            throw new InvalidOperationException("Choose a supported scenery setting.");
        if (FlareStyle is not ("modern" or "original"))
            throw new InvalidOperationException("Choose a supported lens flare style.");
    }

    public void ApplyTo(LauncherSettings s)
    {
        Validate();
        s.Width=Width; s.Height=Height; s.WindowMode=WindowMode;
        s.Fullscreen=WindowMode!="windowed";
        s.AntiAliasing=AntiAliasing; s.AnisotropicFiltering=AnisotropicFiltering;
        s.DrawDistance=DrawDistance;
        s.DynamicLighting=DynamicLighting; s.Shadows=Shadows; s.Headlights=Headlights;
        s.WaterDetail=WaterDetail; s.CloudDetail=CloudDetail;
        s.FlareStyle=FlareStyle;
    }
}
