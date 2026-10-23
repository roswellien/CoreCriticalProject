using System.ComponentModel;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Threading;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

public partial class ControllerWindow : Window
{
    private readonly string dataRoot;
    private ControllerInput? input;
    private readonly DispatcherTimer timer = new() { Interval = TimeSpan.FromMilliseconds(33) };
    private ControllerCalibration? calibration;
    private ControllerDevice? selected;
    private CalibrationCapture? capture;
    private bool range, updating, dirty, ready;
    private DateTime scanAfter, restStarted;
    private int axisIndex;
    private static readonly string[] AxisNames = ["Left stick X", "Left stick Y", "Right stick X", "Right stick Y", "Left trigger", "Right trigger"];
    internal static readonly string[] ButtonNames = ["South (A / Cross)", "East (B / Circle)", "West (X / Square)", "North (Y / Triangle)",
        "Back / Share", "Guide / PS", "Start / Options", "Left stick", "Right stick", "Left shoulder", "Right shoulder",
        "D-pad up", "D-pad down", "D-pad left", "D-pad right", "Misc 1", "Right paddle 1", "Left paddle 1", "Right paddle 2", "Left paddle 2",
        "Touchpad", "Misc 2", "Misc 3", "Misc 4", "Misc 5", "Misc 6"];
    public sealed class AxisRow : INotifyPropertyChanged
    {
        public string Name { get; init; } = "";
        public string Raw { get; private set; } = "—";
        public string Adjusted { get; private set; } = "—";
        public event PropertyChangedEventHandler? PropertyChanged;
        public void Update(string raw, string adjusted)
        {
            Raw = raw; Adjusted = adjusted; PropertyChanged?.Invoke(this, new(nameof(Raw))); PropertyChanged?.Invoke(this, new(nameof(Adjusted)));
        }
    }
    private readonly AxisRow[] rows = AxisNames.Select(n => new AxisRow { Name = n }).ToArray();
    public ControllerWindow(string root)
    {
        dataRoot = root; InitializeComponent(); Axes.ItemsSource = rows; Axes.SelectedIndex = 0; ready = true;
        timer.Tick += (_, _) => Poll();
        Loaded += (_, _) =>
        {
            try { input = new(); timer.Start(); Poll(); }
            catch (Exception ex) { Status.Text = ex.Message; }
        };
        Deactivated += (_, _) =>
        {
            ClearReadings();
            if (capture != null) { CancelCalibration(); Status.Text = "Calibration canceled because this window lost focus. Start again when ready."; }
        };
        Closing += OnClosing;
        Closed += (_, _) => { timer.Stop(); input?.Dispose(); };
    }
    private bool Discard() => !dirty || MessageBox.Show(this, "Discard unsaved controller calibration?", "Unsaved calibration", MessageBoxButton.YesNo) == MessageBoxResult.Yes;
    private void OnClosing(object? sender, CancelEventArgs e) { if (!Discard()) e.Cancel = true; }
    private void ClearReadings() { foreach (var row in rows) row.Update("—", "—"); Buttons.Text = "Buttons: —"; }
    private void Poll()
    {
        if (input == null || !IsActive) return;
        try
        {
            if (DateTime.UtcNow >= scanAfter)
            {
                scanAfter = DateTime.UtcNow.AddSeconds(1);
                IReadOnlyList<ControllerDevice> list = input.Scan();
                // Keep an edited device selected after unplugging. A hotplug must not discard the draft
                // or silently apply it to the next controller in the enumeration.
                if (dirty && selected != null && list.All(d => d.Instance != selected.Instance))
                    list = list.Append(selected with { Name = selected.Name.Replace(" — disconnected", "") + " — disconnected" }).ToArray();
                var old = Devices.ItemsSource as IReadOnlyList<ControllerDevice>;
                if (old == null || !old.SequenceEqual(list))
                {
                    var previous = selected;
                    updating = true; Devices.ItemsSource = list;
                    Devices.SelectedItem = list.FirstOrDefault(d => d.Instance == previous?.Instance) ?? list.FirstOrDefault(); updating = false;
                    if (previous?.Instance != (Devices.SelectedItem as ControllerDevice)?.Instance)
                    {
                        // Never carry an in-progress capture or dirty calibration onto another physical device.
                        dirty = false; SelectDevice();
                    }
                }
                if (list.Count == 0) Status.Text = "No controller detected. Connect an Xbox or PlayStation controller by USB or pair it in Windows, then return here.";
            }
            if (selected == null || calibration == null) return;
            var state = input.Read(selected.Instance);
            if (state == null) { ClearReadings(); CancelCalibration(); Status.Text = "Controller disconnected. Reconnect it to continue."; return; }
            if (capture != null)
            {
                if (range) capture.Range(state.Axes);
                else { capture.Rest(state.Axes); Next.IsEnabled = DateTime.UtcNow - restStarted >= TimeSpan.FromSeconds(1.2); }
            }
            for (int i = 0; i < 6; i++) rows[i].Update(state.Axes[i].ToString(), calibration.Axes[i].Adjust(state.Axes[i], i >= 4).ToString("0.000"));
            string pressed = string.Join(", ", ButtonNames.Where((_, i) => state.Buttons[i]));
            Buttons.Text = "Buttons: " + (pressed.Length == 0 ? "none pressed" : pressed);
        }
        catch (Exception ex)
        {
            timer.Stop(); CancelCalibration(); Tuning.IsEnabled = false; ClearReadings();
            Status.Text = "Controller test stopped. Close and reopen setup to retry. " + ex.Message;
        }
    }
    private void DeviceChanged(object sender, SelectionChangedEventArgs e)
    {
        if (!ready || updating) return;
        if (!Discard())
        {
            updating = true; Devices.SelectedItem = (Devices.ItemsSource as IEnumerable<ControllerDevice>)?.FirstOrDefault(d => d.Instance == selected?.Instance); updating = false; return;
        }
        dirty = false; SelectDevice();
    }
    private void SelectDevice()
    {
        CancelCalibration(); ClearReadings(); selected = Devices.SelectedItem as ControllerDevice; calibration = null; Tuning.IsEnabled = false;
        if (selected == null) { IdentityNotice.Text = ""; return; }
        try
        {
            calibration = ControllerCalibration.Load(dataRoot, selected.Key); Tuning.IsEnabled = true;
            IdentityNotice.Text = selected.HasSerial ? "Calibration follows this controller's reported identity." :
                "No unique serial number is available. Calibration is tied to this connection; changing ports or transport may require calibrating again.";
            Status.Text = "Move the sticks and press buttons to test. Start calibration to measure resting centers and full range.";
            ShowTuning();
        }
        catch (Exception ex) { Status.Text = "Saved calibration could not be loaded; the file is preserved. " + ex.Message; }
    }
    private void AxisChanged(object sender, SelectionChangedEventArgs e)
    {
        axisIndex = Math.Max(0, Axes.SelectedIndex); if (ready) ShowTuning();
    }
    private void ShowTuning()
    {
        if (calibration == null) return;
        updating = true; var axis = calibration.Axes[axisIndex]; AxisTitle.Text = AxisNames[axisIndex];
        Deadzone.Value = axis.Deadzone; Response.Value = axis.Response; Invert.IsChecked = axis.Inverted;
        DeadzoneLabel.Text = axis.Deadzone.ToString("P0"); ResponseLabel.Text = axis.Response.ToString("0.00"); updating = false;
    }
    private void Tune(object sender, RoutedPropertyChangedEventArgs<double> e)
    {
        if (!ready || updating || calibration == null) return;
        calibration.Axes[axisIndex].Deadzone = Deadzone.Value; calibration.Axes[axisIndex].Response = Response.Value;
        DeadzoneLabel.Text = Deadzone.Value.ToString("P0"); ResponseLabel.Text = Response.Value.ToString("0.00"); dirty = true;
    }
    private void InvertChanged(object sender, RoutedEventArgs e)
    {
        if (!ready || updating || calibration == null) return;
        calibration.Axes[axisIndex].Inverted = Invert.IsChecked == true; dirty = true;
    }
    private void StartCalibration(object sender, RoutedEventArgs e)
    {
        capture = new(); range = false; restStarted = DateTime.UtcNow;
        Next.Content = "Measure full range"; Next.IsEnabled = false; Save.IsEnabled = false;
        Status.Text = "Release both sticks and triggers. Leave them untouched for a moment, then choose Measure full range.";
    }
    private void NextCalibration(object sender, RoutedEventArgs e)
    {
        if (capture == null || selected == null) return;
        if (!range)
        {
            range = true; Next.Content = "Finish calibration";
            Status.Text = "Rotate both sticks through full circles and press each trigger fully several times. Then choose Finish calibration."; return;
        }
        try
        {
            var measured = capture.Finish(selected.Key);
            // Measurement replaces ranges/centers, retaining the user's tuning choices.
            for (int i = 0; i < 6; i++) if (calibration != null)
            {
                measured.Axes[i].Deadzone = calibration.Axes[i].Deadzone; measured.Axes[i].Response = calibration.Axes[i].Response;
                measured.Axes[i].Inverted = calibration.Axes[i].Inverted;
            }
            calibration = measured; dirty = true; CancelCalibration(); ShowTuning();
            Status.Text = "Calibration measured. Test the adjusted values, then save when satisfied.";
        }
        catch (Exception ex) { CancelCalibration(); Status.Text = ex.Message + " Start calibration again to retry."; }
    }
    private void CancelCalibration() { capture = null; range = false; Next.IsEnabled = false; Next.Content = "Measure full range"; Save.IsEnabled = true; }
    private void SaveCalibration(object sender, RoutedEventArgs e)
    {
        if (calibration == null) return;
        try { calibration.Save(dataRoot); dirty = false; Status.Text = "Calibration saved for this device. Configure gameplay through MW3 bindings."; }
        catch (Exception ex) { Status.Text = "Calibration could not be saved. " + ex.Message; }
    }
    private void CloseWindow(object sender, RoutedEventArgs e) => Close();
    private void OpenBindings(object sender, RoutedEventArgs e)
    {
        if (capture != null) { CancelCalibration(); Status.Text = "Measurement canceled. Finish and save calibration before testing gameplay."; }
        if (dirty) { Status.Text = "Save your calibration before opening MW3 bindings so gameplay uses the same settings."; return; }
        new ControllerBindingsWindow(dataRoot, selected) { Owner = this }.ShowDialog();
    }
}

