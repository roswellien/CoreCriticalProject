using System.ComponentModel;
using System.Windows;
using System.Windows.Automation;
using System.Windows.Media.Animation;
using System.Windows.Shapes;

namespace MW3RemasterLauncher;

/// <summary>Clockwise backlighting of the stationary four-section brand mark.</summary>
public partial class CoreCriticalLoadingMark : System.Windows.Controls.UserControl
{
    public static readonly DependencyProperty IsActiveProperty = DependencyProperty.Register(
        nameof(IsActive), typeof(bool), typeof(CoreCriticalLoadingMark),
        new PropertyMetadata(false, (o, _) => ((CoreCriticalLoadingMark)o).Refresh()));
    public bool IsActive { get => (bool)GetValue(IsActiveProperty); set => SetValue(IsActiveProperty, value); }
    private readonly Storyboard _cycle = new() { Duration = TimeSpan.FromSeconds(2.8), RepeatBehavior = RepeatBehavior.Forever };
    private Window? _window;
    private bool _running;

    public CoreCriticalLoadingMark()
    {
        InitializeComponent();
        var sections = new[] { LightTopRight, LightBottomRight, LightBottomLeft, LightTopLeft };
        for (var i = 0; i < sections.Length; i++)
        {
            var start = i * .7;
            var pulse = new DoubleAnimationUsingKeyFrames { Duration = _cycle.Duration };
            pulse.KeyFrames.Add(new DiscreteDoubleKeyFrame(0, KeyTime.FromTimeSpan(TimeSpan.Zero)));
            if (start > 0) pulse.KeyFrames.Add(new DiscreteDoubleKeyFrame(0, KeyTime.FromTimeSpan(TimeSpan.FromSeconds(start))));
            pulse.KeyFrames.Add(new EasingDoubleKeyFrame(1, KeyTime.FromTimeSpan(TimeSpan.FromSeconds(start + .28)),
                new SineEase { EasingMode = EasingMode.EaseInOut }));
            pulse.KeyFrames.Add(new EasingDoubleKeyFrame(0, KeyTime.FromTimeSpan(TimeSpan.FromSeconds(start + .64)),
                new SineEase { EasingMode = EasingMode.EaseInOut }));
            pulse.KeyFrames.Add(new DiscreteDoubleKeyFrame(0, KeyTime.FromTimeSpan(TimeSpan.FromSeconds(2.8))));
            Storyboard.SetTarget(pulse, sections[i]);
            Storyboard.SetTargetProperty(pulse, new PropertyPath(OpacityProperty));
            _cycle.Children.Add(pulse);
        }
        Loaded += (_, _) =>
        {
            _window = Window.GetWindow(this);
            if (_window != null) _window.StateChanged += WindowStateChanged;
            SystemParameters.StaticPropertyChanged += PreferencesChanged;
            Refresh();
        };
        Unloaded += (_, _) =>
        {
            if (_window != null) _window.StateChanged -= WindowStateChanged;
            SystemParameters.StaticPropertyChanged -= PreferencesChanged;
            _window = null;
            Stop();
        };
        IsVisibleChanged += (_, _) => Refresh();
    }

    private void WindowStateChanged(object? sender, EventArgs e) => Refresh();
    private void PreferencesChanged(object? sender, PropertyChangedEventArgs e)
    {
        if (e.PropertyName == nameof(SystemParameters.ClientAreaAnimation)) Refresh();
    }
    private void Stop()
    {
        if (_running) _cycle.Remove(this);
        _running = false;
        foreach (var section in new[] { LightTopRight, LightBottomRight, LightBottomLeft, LightTopLeft })
        {
            section.BeginAnimation(OpacityProperty, null);
            section.Opacity = 0;
        }
    }
    private void Refresh()
    {
        if (!Dispatcher.CheckAccess()) { Dispatcher.BeginInvoke(new Action(Refresh)); return; }
        if (LightTopRight == null) return;
        AutomationProperties.SetItemStatus(this, IsActive ? "Preparing game" : "Idle");
        var visible = IsLoaded && IsVisible && _window?.WindowState != WindowState.Minimized;
        if (!IsActive || !visible || !SystemParameters.ClientAreaAnimation)
        {
            Stop();
            if (IsActive && visible && !SystemParameters.ClientAreaAnimation)
                foreach (var section in new[] { LightTopRight, LightBottomRight, LightBottomLeft, LightTopLeft }) section.Opacity = .45;
            return;
        }
        if (_running) return;
        _cycle.Begin(this, true);
        _running = true;
    }
}
