using System.IO;
using System.Runtime.ExceptionServices;
using System.Windows;
using System.Windows.Automation;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;
using MW3RemasterLauncher;
using MW3RemasterLauncher.Core;

static class GraphicsSetupUiChecks
{
    public static void RunHeadlights(string root) => RunWithWpfApp(app => ExecuteHeadlights(app, root));

    public static void RunControlsUi(string root) => RunWithWpfApp(app => ExecuteControlsUi(app, root));

    public static void RunControlsAndHeadlights(string headlightsRoot, string controlsRoot) => RunWithWpfApp(app =>
    {
        ExecuteHeadlights(app, headlightsRoot);
        ExecuteControlsUi(app, controlsRoot);
    });

    private static void RunWithWpfApp(Action<App> body)
    {
        ExceptionDispatchInfo failure = null!;
        var thread = new Thread(() =>
        {
            try
            {
                var app = new App(false);
                // Keep shutdown explicit even when a failed check leaves a window open.
                app.ShutdownMode = ShutdownMode.OnExplicitShutdown;
                app.InitializeComponent();
                body(app);
                app.Shutdown();
            }
            // Let the STA exit without closing windows that may have unsaved changes.
            catch (Exception error) { failure = ExceptionDispatchInfo.Capture(error); }
        });
        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();
        thread.Join();
        failure?.Throw();
    }

    private static void ExecuteHeadlights(App app, string root)
    {
        root = Path.GetFullPath(root);
        Directory.CreateDirectory(root);
        var panel = new GraphicsPreferencesPanel();
        var window = new Window
        {
            Title = "Headlight graphics check", Width = 520, Height = 980,
            Content = panel, ShowActivated = false, Left = -10000
        };
        window.Show();
        try
        {
            panel.Load(new LauncherSettings { DynamicLighting = true, Headlights = true });
            var vsync = (CheckBox)panel.FindName("ChkVsync");
            Check(vsync.IsChecked == false && !panel.Read().Vsync, "VSync must default off in Display.");
            vsync.IsChecked = true;
            Check(panel.Read().Vsync, "VSync checkbox did not reach graphics preferences.");
            panel.Load(new LauncherSettings { DynamicLighting = true, Headlights = true, Vsync = true });
            Check(vsync.IsChecked == true, "Saved VSync choice did not load in Display.");
            var cutscenes = (CheckBox)panel.FindName("ChkUpscaledCutscenes");
            Check(cutscenes.IsChecked == true && panel.Read().UpscaledCutscenes, "Upscaled cutscenes must default on.");
            cutscenes.IsChecked = false;
            Check(!panel.Read().UpscaledCutscenes, "Upscaled cutscenes checkbox did not reach graphics preferences.");
            panel.Load(new LauncherSettings { DynamicLighting = true, Headlights = true, UpscaledCutscenes = false });
            Check(cutscenes.IsChecked == false, "Saved Upscaled cutscenes choice did not load.");
            var master = (CheckBox)panel.FindName("ChkHeadlights");
            var dynamicLighting = (CheckBox)panel.FindName("ChkDynamicLighting");
            Check(master.IsEnabled && master.IsChecked == true && panel.Read().Headlights,
                "Headlight preference not displayed");
            dynamicLighting.IsChecked = false;
            Check(!master.IsEnabled && master.IsChecked == true && panel.Read().Headlights,
                "Dynamic lighting off lost headlight choice");
            dynamicLighting.IsChecked = true;
            window.UpdateLayout();
            Capture(window, Path.Combine(root, "headlight-display.png"));

            var result = RunModal(window, new HeadlightBindingsWindow(root), dialog =>
            {
                dialog.UpdateLayout();
                Check(dialog.ActualHeight >= 480, "Headlight bindings dialog is shorter than 480 DIPs");
                Capture(dialog, Path.Combine(root, "headlight-controls.png"));
                Click(FindButton(dialog, "Headlight mouse binding"));
                RaiseMouseDown(dialog, MouseButton.XButton2);
                var choice = FindMouseChoice(dialog);
                Check(choice.SelectedIndex == 5, "Headlight capture did not select Mouse 5");
                Click(FindButton(dialog, "Save"));
            });
            Check(result == true && new HeadlightBindings(root).Load().Mouse == 5,
                "Headlight Mouse 5 binding was not saved");

            result = RunModal(window, new HeadlightBindingsWindow(root), dialog =>
            {
                var capture = FindButton(dialog, "Headlight mouse binding");
                var choice = FindMouseChoice(dialog);
                Click(capture);
                RaiseWheel(dialog, 120);
                Check(choice.SelectedIndex == 6, "Headlight capture did not select Wheel Up");
                Click(capture);
                RaiseKey(dialog, Key.Escape);
                Check(choice.SelectedIndex == 6, "Canceling headlight capture changed the binding");
                Click(FindButton(dialog, "Clear mouse binding"));
                Check(choice.SelectedIndex == 0, "Clearing the headlight mouse binding did not unassign it");
                choice.SelectedIndex = 7;
                Click(FindButton(dialog, "Save"));
            });
            Check(result == true && new HeadlightBindings(root).Load().Mouse == 7,
                "Headlight Wheel Down binding was not saved");
        }
        finally { window.Close(); }
        Console.WriteLine("Actual WPF Headlights switch, dependency preservation and binding dialog passed.");
    }

    private static void ExecuteControlsUi(App app, string root)
    {
        var store = new ControlProfiles(root);
        store.Save(store.Load());
        var preset = store.Load().Profiles.Single(profile => profile.Name == "MW5-style (MW3)");
        var controls = OpenControlsWindow(root);
        var save = (Button)controls.FindName("SaveButton");
        var completed = false;
        try
        {
            Check(controls.WindowState == WindowState.Maximized, "Controls window did not open maximized");
            var profiles = (ListBox)controls.FindName("Profiles");
            profiles.SelectedItem = profiles.Items.Cast<ControlProfile>().Single(profile => profile.Id == preset.Id);
            var grid = (DataGrid)controls.FindName("Bindings");
            ControlsWindow.BindingRow Row(string action) =>
                grid.Items.Cast<ControlsWindow.BindingRow>().Single(row => row.Action == action);

            Check(grid.Columns.Count == 5 && grid.Columns.Any(column => Equals(column.Header, "Combos")),
                "Controls grid did not display five columns including Combos");
            Check(Row("CMD_ZOOM_LOCK").Mouse == "Middle", "MW5 zoom lock did not display Middle");
            Check(Row("CMD_WEP_NEXT").Mouse == "Wheel Up", "MW5 next weapon did not display Wheel Up");
            Check(Row("CMD_WEP_PREV").Mouse == "Wheel Down", "MW5 previous weapon did not display Wheel Down");
            Check(Row("CMD_JJ_FORWARD").Combos == "W + Space", "MW5 forward jump combo did not display W + Space");
            Check(((CheckBox)controls.FindName("Mw2JumpJets")).IsChecked == true,
                "MW5 layout did not enable MW2 jump jets");

            Check(!RaiseWheel(grid, 120).Handled, "Controls intercepted grid scrolling outside capture");
            var setMouse = FindButton(controls, "Set mouse");
            grid.SelectedItem = Row("CMD_RETICULE_ZOOM");
            Click(setMouse);
            Check(RaiseMouseDown(controls, MouseButton.XButton1).Handled &&
                Row("CMD_RETICULE_ZOOM").Mouse == "Mouse 4", "Controls did not capture Mouse 4 for reticule zoom");

            grid.SelectedItem = Row("CMD_CYCLE_CAM");
            Click(setMouse);
            RaiseMouseDown(controls, MouseButton.XButton1);
            var status = (TextBlock)controls.FindName("Status");
            Check(Row("CMD_CYCLE_CAM").Mouse == "Unassigned" && status.Text.Contains("already assigned"),
                "Controls did not reject a duplicate Mouse 4 binding");

            grid.SelectedItem = Row("CMD_RETICULE_ZOOM");
            Click(FindButton(controls, "Clear mouse"));
            Check(Row("CMD_RETICULE_ZOOM").Mouse == "Unassigned", "Controls did not clear the mouse binding");
            completed = true;
        }
        finally
        {
            if (completed)
            {
                Click(save);
                controls.Close();
            }
        }

        CheckNullableJumpJets(Path.Combine(root, "nulljj"), preset);
        Console.WriteLine("Actual WPF Controls layout, mouse capture, jump jet persistence and combo editor passed.");
    }

    private static void CheckNullableJumpJets(string root, ControlProfile preset)
    {
        var profile = ControlProfiles.Clone(preset, preset.Name);
        profile.Mw2JumpJets = null;
        var store = new ControlProfiles(root);
        store.Save(new ControlDocument { ActiveId = profile.Id, Profiles = [profile] });
        var controls = OpenControlsWindow(root);
        var save = (Button)controls.FindName("SaveButton");
        var completed = false;
        try
        {
            var jumpJets = (CheckBox)controls.FindName("Mw2JumpJets");
            Check(jumpJets.IsChecked == null, "Controls did not display the inherited jump jet state");
            ((TextBox)controls.FindName("ProfileName")).Text = "Null JJ";
            Click(save);
            ControlProfile Reload() => store.Load().Profiles.Single(item => item.Id == profile.Id);

            var renamed = Reload();
            Check(renamed.Name == "Null JJ" && renamed.Mw2JumpJets == null,
                "Renaming the layout did not preserve its inherited jump jet state");
            jumpJets.IsChecked = false;
            Click(save);
            Check(Reload().Mw2JumpJets == false, "Classic jump jet state did not persist");
            jumpJets.IsChecked = true;
            Click(save);
            Check(Reload().Mw2JumpJets == true, "MW2 jump jet state did not persist");
            CheckComboEditor(controls, ControlProfiles.Clone(preset, preset.Name));
            completed = true;
        }
        finally
        {
            if (completed)
            {
                Click(save);
                controls.Close();
            }
        }
    }

    private static ControlsWindow OpenControlsWindow(string root)
    {
        var controls = new ControlsWindow(root, root) { ShowActivated = false, Left = -10000 };
        var initialState = controls.WindowState;
        Check(initialState == WindowState.Maximized, "Controls window did not default to maximized");
        // WPF rejects Show() with both ShowActivated=false and WindowState=Maximized.
        controls.WindowState = WindowState.Normal;
        controls.Show();
        controls.WindowState = initialState;
        controls.UpdateLayout();
        return controls;
    }

    private static void CheckComboEditor(Window owner, ControlProfile profile)
    {
        const string action = "CMD_JJ_UP";
        var binding = profile.Bindings[action];
        var original = System.Text.Json.JsonSerializer.Serialize(binding.Combos);
        var result = RunModal(owner, new ComboEditorWindow(profile, action), dialog =>
        {
            CaptureKey(dialog, Key.LeftShift);
            CaptureKey(dialog, Key.W);
            dialog.SuppressCheckBox.IsChecked = false;
            Click(dialog.AddComboButton);
            Check(dialog.CombosList.Items.Count == 1, "Combo editor did not stage the canceled chord");
            Click(dialog.CancelButton);
        });
        Check(result == false && System.Text.Json.JsonSerializer.Serialize(binding.Combos) == original,
            "Canceling the combo editor changed the profile");

        result = RunModal(owner, new ComboEditorWindow(profile, action), dialog =>
        {
            Check(!dialog.AddComboButton.IsEnabled, "Combo editor enabled Add with no ingredients");
            CaptureKey(dialog, Key.Q);
            Check(!dialog.AddComboButton.IsEnabled, "Combo editor enabled Add with one ingredient");
            CaptureKey(dialog, Key.Q);
            Check(dialog.StatusText.Text.Contains("already in the chord") && !dialog.AddComboButton.IsEnabled,
                "Combo editor did not reject a repeated key");

            Click(dialog.ClearIngredientsButton);
            Click(dialog.CaptureInputButton);
            RaiseWheel(dialog, 120);
            Click(dialog.CaptureInputButton);
            RaiseWheel(dialog, -120);
            Check(dialog.StatusText.Text.Contains("cannot be in the same combo") && !dialog.AddComboButton.IsEnabled,
                "Combo editor did not reject opposing wheel directions");

            Click(dialog.ClearIngredientsButton);
            CaptureKey(dialog, Key.Space);
            CaptureKey(dialog, Key.W);
            Click(dialog.AddComboButton);
            Check(dialog.StatusText.Text.Contains("conflicts with") && dialog.CombosList.Items.Count == 0,
                "Combo editor did not reject the reversed forward jump chord");

            Click(dialog.ClearIngredientsButton);
            CaptureKey(dialog, Key.LeftCtrl);
            Click(dialog.CaptureInputButton);
            RaiseMouseDown(dialog, MouseButton.XButton1);
            Click(dialog.CaptureInputButton);
            RaiseWheel(dialog, 120);
            dialog.SuppressCheckBox.IsChecked = false;
            Click(dialog.AddComboButton);

            CaptureKey(dialog, Key.Q);
            CaptureKey(dialog, Key.E);
            Click(dialog.AddComboButton);
            Check(dialog.CombosList.Items.Count == 2, "Combo editor did not stage both valid chords");
            dialog.CombosList.SelectedIndex = 1;
            Click(dialog.RemoveSelectedButton);
            Click(dialog.OkButton);
        });
        Check(result == true && binding.Combos is [{ Inputs.Count: 3, Suppress: false }],
            "Combo editor did not apply only the three-input pass-through chord");
    }

    private static bool? RunModal<T>(Window owner, T dialog, Action<T> body) where T : Window
    {
        dialog.Owner = owner;
        dialog.ShowActivated = false;
        dialog.WindowStartupLocation = WindowStartupLocation.Manual;
        dialog.Left = -10000;
        ExceptionDispatchInfo failure = null!;
        owner.Dispatcher.BeginInvoke(new Action(() =>
        {
            try { body(dialog); }
            catch (Exception error)
            {
                failure = ExceptionDispatchInfo.Capture(error);
                // Hiding ends the modal loop without running window-closing handlers.
                if (dialog.IsVisible) dialog.Hide();
            }
            if (failure == null && dialog.IsVisible) dialog.Close();
        }));
        var result = dialog.ShowDialog();
        failure?.Throw();
        return result;
    }

    private static IEnumerable<T> LogicalChildren<T>(DependencyObject parent) where T : FrameworkElement
    {
        foreach (var child in LogicalTreeHelper.GetChildren(parent).OfType<DependencyObject>())
        {
            if (child is T match) yield return match;
            foreach (var descendant in LogicalChildren<T>(child)) yield return descendant;
        }
    }

    private static Button FindButton(Window window, string label) =>
        LogicalChildren<Button>(window).Single(button =>
            AutomationProperties.GetName(button) == label || Equals(button.Content, label));

    private static ComboBox FindMouseChoice(Window window) => LogicalChildren<ComboBox>(window).Single(
        choice => AutomationProperties.GetName(choice) == "Headlight mouse choice");

    private static void Click(Button button) => button.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));

    private static MouseButtonEventArgs RaiseMouseDown(UIElement target, MouseButton button)
    {
        var args = new MouseButtonEventArgs(Mouse.PrimaryDevice, Environment.TickCount, button)
            { RoutedEvent = Mouse.PreviewMouseDownEvent };
        target.RaiseEvent(args);
        return args;
    }

    private static MouseWheelEventArgs RaiseWheel(UIElement target, int delta)
    {
        var args = new MouseWheelEventArgs(Mouse.PrimaryDevice, Environment.TickCount, delta)
            { RoutedEvent = Mouse.PreviewMouseWheelEvent };
        target.RaiseEvent(args);
        return args;
    }

    private static void CaptureKey(ComboEditorWindow dialog, Key key)
    {
        Click(dialog.CaptureInputButton);
        RaiseKey(dialog, key);
    }

    private static void RaiseKey(Window window, Key key) => window.RaiseEvent(
        new KeyEventArgs(Keyboard.PrimaryDevice, PresentationSource.FromVisual(window), Environment.TickCount, key)
        { RoutedEvent = Keyboard.PreviewKeyDownEvent });

    private static void Check(bool condition, string message)
    {
        if (!condition) throw new Exception(message);
    }

    public static void Run(string root,string game)
    {
        var flareStyleReviewCases = new[]
        {
            (Value: "modern", Expected: "Lens flare alpha: Smooth"),
            (Value: "original", Expected: "Lens flare alpha: Original"),
            (Value: "future", Expected: "Lens flare alpha: Invalid (future)")
        };
        foreach (var (value, expected) in flareStyleReviewCases)
            if (GameSetupWindow.LensFlareStyleReviewText(value) != expected)
                throw new Exception($"Lens flare review text for '{value}' was not '{expected}'");

        root=Path.GetFullPath(root);Directory.CreateDirectory(root);
        var manager=new SettingsManager(root,root);
        manager.Current.GamePath=Path.GetFullPath(game);
        manager.Current.InitialSetupCompleted=false;
        manager.Save();
        Exception failure=null!;
        var thread=new Thread(()=>{
            var app=new App(false);app.InitializeComponent();
            var window=new MainWindow(root){ShowActivated=false,ShowInTaskbar=false,
                WindowStartupLocation=WindowStartupLocation.Manual,Left=-10000,Top=100,Height=1050};
            var timer=new DispatcherTimer{Interval=TimeSpan.FromMilliseconds(100)};
            var ticks=0;var phase=0;
            timer.Tick+=(_,_)=>{
                try{
                    if(++ticks>300)throw new Exception("Setup did not finish in the bounded UI check");
                    if(phase==0){
                        var setup=app.Windows.OfType<GameSetupWindow>().FirstOrDefault();
                        if(setup==null)return;
                        var panel=(GraphicsPreferencesPanel)setup.FindName("SetupGraphics");
                        panel.Load(new LauncherSettings { FlareStyle="original" });
                        if(panel.Read().FlareStyle!="original")throw new Exception("Lens flare style selection was not displayed");
                        if(panel.Read().DynamicLighting||panel.Read().Shadows)throw new Exception("Fresh setup lighting is not stock");
                        var before=File.ReadAllBytes(manager.SettingsPath);
                        var next=(Button)setup.FindName("ContinueButton");
                        var path=(TextBox)setup.FindName("ExistingPath");
                        var originalPath=path.Text;path.Text="";
                        next.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
                        if(((Grid)setup.FindName("GameFilesStep")).Visibility!=Visibility.Visible || setup.GameDirectory!=null)
                            throw new Exception("Incomplete game source advanced or started setup");
                        ((RadioButton)setup.FindName("MediaChoice")).IsChecked=true;
                        next.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
                        if(((Grid)setup.FindName("GameFilesStep")).Visibility!=Visibility.Visible)
                            throw new Exception("Missing ISO/patch advanced the setup wizard");
                        ((RadioButton)setup.FindName("ExistingChoice")).IsChecked=true;
                        path.Text=originalPath;
                        setup.UpdateLayout();Capture(setup,Path.Combine(root,"setup-game-files.png"));
                        next.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
                        if(((Grid)setup.FindName("GraphicsStep")).Visibility!=Visibility.Visible)
                            throw new Exception("Game files did not advance to graphics");
                        panel.Load(new LauncherSettings{Width=2560,Height=1440,WindowMode="windowed",
                            AntiAliasing="4",AnisotropicFiltering=8,DrawDistance=2400,FogDistance=0,
                            DynamicLighting=true,Shadows=true,FlareStyle="original"});
                        var selected=panel.Read();
                        if(selected.Width!=2560||selected.WindowMode!="windowed"||
                           selected.AntiAliasing!="4"||selected.DrawDistance!=2400||selected.FlareStyle!="original"||
                           selected.AnisotropicFiltering!=8||!selected.DynamicLighting||!selected.Shadows)
                            throw new Exception("Setup controls do not capture all graphics choices");
                        next.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
                        if(((Grid)setup.FindName("PacksStep")).Visibility!=Visibility.Visible || setup.GameDirectory!=null || setup.SelectedGraphics!=null)
                            throw new Exception("Setup started before optional packs and review");
                        ((Button)setup.FindName("BackButton")).RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
                        if(panel.Read()!=selected || ((Grid)setup.FindName("GraphicsStep")).Visibility!=Visibility.Visible)
                            throw new Exception("Back navigation lost graphics choices");
                        setup.Height=1050;setup.UpdateLayout();Capture(setup,Path.Combine(root,"setup-graphics.png"));
                        setup.DialogResult=false;
                        if(!before.SequenceEqual(File.ReadAllBytes(manager.SettingsPath)))throw new Exception("Cancelling setup changed settings");
                        phase=1;return;
                    }
                    if(phase==2){
                        var finish=app.Windows.OfType<GameSetupWindow>().FirstOrDefault();
                        if(finish==null)return;
                        var next=(Button)finish.FindName("ContinueButton");
                        next.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
                        ((GraphicsPreferencesPanel)finish.FindName("SetupGraphics")).Load(
                            new LauncherSettings{Width=2560,Height=1440,WindowMode="windowed",
                                AntiAliasing="4",AnisotropicFiltering=8,DrawDistance=2400,FogDistance=0,
                                DynamicLighting=true,Shadows=true,FlareStyle="original"});
                        next.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
                        finish.UpdateLayout();Capture(finish,Path.Combine(root,"setup-optional-packs.png"));
                        next.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
                        if(((Grid)finish.FindName("ReviewStep")).Visibility!=Visibility.Visible || finish.GameDirectory!=null ||
                           !((TextBlock)finish.FindName("ReviewGraphics")).Text.Contains("2560 × 1440") ||
                           !((TextBlock)finish.FindName("ReviewGraphics")).Text.Contains("Lens flare alpha: Original") ||
                           !((TextBlock)finish.FindName("ReviewPacks")).Text.Contains("stock content"))
                            throw new Exception("Review did not show the selected choices before installation");
                        finish.UpdateLayout();Capture(finish,Path.Combine(root,"setup-review.png"));
                        phase=3;
                        ((Button)finish.FindName("ContinueButton")).RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
                        return;
                    }
                    if(phase==3){
                        if(app.Windows.OfType<GameSetupWindow>().Any())return;
                        var completed=new SettingsManager(root,root).Current;
                        var expected=new GraphicsPreferences(2560,1440,"windowed","4",8,
                            2400,true,true,FlareStyle:"original");
                        if(!completed.InitialSetupCompleted||GraphicsPreferences.From(completed)!=expected)
                            throw new Exception("Successful setup did not save all first-launch graphics choices");
                        var actual=(GraphicsPreferencesPanel)window.FindName("DisplayGraphics");
                        if(actual.Read()!=expected)throw new Exception("Display did not reload completed setup choices");
                        timer.Stop();window.Close();return;
                    }
                    ((RadioButton)window.FindName("TabGraphics")).IsChecked=true;
                    var display=(GraphicsPreferencesPanel)window.FindName("DisplayGraphics");
                    var lighting=(CheckBox)display.FindName("ChkDynamicLighting");
                    var shadows=(CheckBox)display.FindName("ChkShadows");
                    var waterDetail=(CheckBox)display.FindName("ChkWaterDetail");
                    var cloudDetail=(CheckBox)display.FindName("ChkCloudDetail");
                    if(waterDetail.IsChecked!=true||cloudDetail.IsChecked!=true)
                        throw new Exception("Surface detail did not default on in the graphics panel");
                    waterDetail.IsChecked=false;
                    if(new SettingsManager(root,root).Current.WaterDetail)
                        throw new Exception("Water detail choice was not saved");
                    waterDetail.IsChecked=true;
                    lighting.IsChecked=true;shadows.IsChecked=true;
                    var saved=new SettingsManager(root,root).Current;
                    if(!saved.DynamicLighting||!saved.Shadows)throw new Exception("Display choices were not saved");
                    lighting.IsChecked=false;
                    saved=new SettingsManager(root,root).Current;
                    if(saved.DynamicLighting||!saved.Shadows||shadows.IsEnabled)throw new Exception("Lighting off lost the shadow choice or left it enabled");
                    lighting.IsChecked=true;
                    window.UpdateLayout();Capture(window,Path.Combine(root,"display-graphics.png"));
                    if(new SettingsManager(root,root).Current.InitialSetupCompleted)throw new Exception("Cancelled setup was marked complete");
                    phase=2;
                    app.Dispatcher.BeginInvoke(new Action(()=>
                        ((Button)window.FindName("BtnImportMedia")).RaiseEvent(new RoutedEventArgs(Button.ClickEvent))));
                }catch(Exception error){failure=error;timer.Stop();foreach(var child in app.Windows.OfType<Window>().ToArray())child.Close();app.Shutdown();}
            };
            timer.Start();app.Run(window);
        });
        thread.SetApartmentState(ApartmentState.STA);thread.Start();thread.Join();
        if(failure!=null)throw failure;
        Console.WriteLine("Actual WPF sequential setup, source validation, graphics/back preservation, optional packs and review before install, original-file verification, save/reload and cancellation passed.");
    }

    private static void Capture(Window window,string path)
    {
        var image=new RenderTargetBitmap((int)window.ActualWidth,(int)window.ActualHeight,96,96,PixelFormats.Pbgra32);
        image.Render(window);var encoder=new PngBitmapEncoder();encoder.Frames.Add(BitmapFrame.Create(image));
        using var file=File.Create(path);encoder.Save(file);
    }
}
