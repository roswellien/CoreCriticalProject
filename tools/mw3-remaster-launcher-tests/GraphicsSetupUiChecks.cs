using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;
using MW3RemasterLauncher;
using MW3RemasterLauncher.Core;

static class GraphicsSetupUiChecks
{
    public static void Run(string root,string game)
    {
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
                            DynamicLighting=true,Shadows=true});
                        var selected=panel.Read();
                        if(selected.Width!=2560||selected.WindowMode!="windowed"||selected.AntiAliasing!="4"||
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
                                DynamicLighting=true,Shadows=true});
                        next.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
                        finish.UpdateLayout();Capture(finish,Path.Combine(root,"setup-optional-packs.png"));
                        next.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
                        if(((Grid)finish.FindName("ReviewStep")).Visibility!=Visibility.Visible || finish.GameDirectory!=null ||
                           !((TextBlock)finish.FindName("ReviewGraphics")).Text.Contains("2560 × 1440") ||
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
                        var expected=new GraphicsPreferences(2560,1440,"windowed","4",8,2400,0,true,true);
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
