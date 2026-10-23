using System.Windows;
using System.Windows.Controls;
using MW3RemasterLauncher.Core;

namespace MW3RemasterLauncher;

/// <summary>Game actions remain separate from device calibration and keyboard layouts.</summary>
public sealed class ControllerBindingsWindow : Window
{
    private bool dirty;
    private sealed record AxisSource(int Id,string Name);
    private sealed record ActionChoice(int Command,string Label);
    private static string ActionLabel(ControlAction action) => action.Command switch {
        0 => "Unassigned",12 => "Jump jets",27 => "Stop / zero throttle",36 => "Full throttle",
        61 => "Fire selected weapon group",63 => "Power up / shut down",70 => "Next enemy target",81 => "Pause",
        >=44 and <=48 => "Select weapon group " + (action.Command-43),_ => action.Label
    };
    public ControllerBindingsWindow(string root, ControllerDevice? device)
    {
        Title = "MW3 controller bindings — Core Critical"; Width = 820; Height = 760; MinWidth = 680; MinHeight = 600;
        WindowStartupLocation = WindowStartupLocation.CenterOwner;
        SetResourceReference(BackgroundProperty,"BrushGround"); SetResourceReference(ForegroundProperty,"BrushInk");
        SetResourceReference(FontFamilyProperty,"FontBody"); FontSize = 14;
        if(device is { CanBind: false })
        {
            Content = new TextBlock { Text = "This controller cannot be selected reliably across processes. Disconnect duplicate devices or try a direct USB connection, then reopen setup. Live input testing is still available.",TextWrapping=TextWrapping.Wrap,Margin=new(24) };return;
        }
        var store = new ControllerProfiles(root); ControllerProfile profile;
        try { profile = store.Load(); }
        catch (Exception ex) { Content = new TextBlock { Text = "Saved layout could not be loaded and is preserved. " + ex.Message, TextWrapping = TextWrapping.Wrap, Margin = new(24) }; return; }
        if (device != null && profile.DeviceKey != device.Key) { profile.DeviceKey = device.Key; profile.Enabled = false; dirty = true; }
        var grid = new Grid { Margin = new(24) }; Content = grid;
        grid.RowDefinitions.Add(new() { Height = GridLength.Auto }); grid.RowDefinitions.Add(new() { Height = new(1,GridUnitType.Star) }); grid.RowDefinitions.Add(new() { Height = GridLength.Auto });
        var head = new StackPanel(); grid.Children.Add(head);
        head.Children.Add(new TextBlock { Text = "MECHWARRIOR 3 · CONTROLLER", FontSize = 22, Margin = new(0,0,0,12) });
        head.Children.Add(new TextBlock { Text = device == null ? "Editing the saved MW3 layout. Select a connected controller in setup to choose a device." : "Controller: " + device.Name, TextWrapping = TextWrapping.Wrap });
        head.Children.Add(new TextBlock { Text = "Throttle returns to zero when released. Keyboard and mouse remain available for menus. Requires the controller-enabled native runtime.", TextWrapping = TextWrapping.Wrap, Margin = new(0,8,0,12) });
        var enabled = new CheckBox { Content = "Use this controller layout for MW3 on the next launch", IsChecked = profile.Enabled, IsEnabled = profile.DeviceKey.Length == 64 };
        enabled.Checked += (_,_)=>dirty=true; enabled.Unchecked += (_,_)=>dirty=true; head.Children.Add(enabled);
        var rows = new StackPanel { Margin = new(0,16,12,12) };
        var scroll = new ScrollViewer { Content = rows, VerticalScrollBarVisibility = ScrollBarVisibility.Auto }; Grid.SetRow(scroll,1); grid.Children.Add(scroll);
        var actions = new[] { new ControlAction("CMD_UNASSIGNED",0) }.Concat(ControlProfiles.Actions).Select(a=>new ActionChoice(a.Command,ActionLabel(a))).ToArray();
        void ActionRow(string label,int value,Action<int> change)
        {
            var row = new Grid { Margin = new(0,0,0,8) }; row.ColumnDefinitions.Add(new() { Width = new(230) }); row.ColumnDefinitions.Add(new());
            row.Children.Add(new TextBlock { Text = label, VerticalAlignment = VerticalAlignment.Center, TextWrapping = TextWrapping.Wrap });
            var combo = new ComboBox { ItemsSource = actions, DisplayMemberPath = "Label", SelectedValuePath = "Command", SelectedValue = value, MaxDropDownHeight = 300 };
            System.Windows.Automation.AutomationProperties.SetName(combo,label+" action");
            combo.SelectionChanged += (_,_)=>{if(combo.SelectedValue is int command){change(command);dirty=true;}};
            Grid.SetColumn(combo,1);row.Children.Add(combo);rows.Children.Add(row);
        }
        for(int i=0;i<26;i++){int index=i;ActionRow(ControllerWindow.ButtonNames[i],profile.Buttons[i],v=>profile.Buttons[index]=v);}
        for(int i=0;i<2;i++){int index=i;ActionRow(i==0?"Left trigger":"Right trigger",profile.Triggers[i],v=>profile.Triggers[index]=v);}
        rows.Children.Add(new TextBlock { Text = "STICK ASSIGNMENTS", Margin = new(0,16,0,12), FontSize = 18 });
        var sources = new[] { new AxisSource(-1,"Unassigned"),new(0,"Left stick X"),new(1,"Left stick Y"),new(2,"Right stick X"),new(3,"Right stick Y") };
        string[] names = ["Throttle","Steering","Torso yaw","Torso pitch"];
        for(int i=0;i<4;i++)
        {
            int index=i;var row = new StackPanel { Margin = new(0,0,0,12) };
            row.Children.Add(new TextBlock { Text = names[i],Margin = new(0,0,0,6) });
            var combo = new ComboBox { ItemsSource = sources,DisplayMemberPath = "Name",SelectedValuePath = "Id",SelectedValue = profile.Axes[i] };
            System.Windows.Automation.AutomationProperties.SetName(combo,names[i]+" stick axis");
            combo.SelectionChanged += (_,_)=>{if(combo.SelectedValue is int axis){profile.Axes[index]=axis;dirty=true;}};row.Children.Add(combo);
            var invert = new CheckBox { Content = "Reverse direction",IsChecked = profile.Scale[i]<0,Margin = new(0,8,0,6) };
            invert.Checked += (_,_)=>{profile.Scale[index]=-Math.Abs(profile.Scale[index]);dirty=true;};
            invert.Unchecked += (_,_)=>{profile.Scale[index]=Math.Abs(profile.Scale[index]);dirty=true;};row.Children.Add(invert);
            var sensitivity = new Slider { Minimum = .1,Maximum = 2,Value = Math.Abs(profile.Scale[i]) };
            var label = new TextBlock { Text = "Sensitivity: "+sensitivity.Value.ToString("0.00") };
            System.Windows.Automation.AutomationProperties.SetName(sensitivity,names[i]+" sensitivity");
            sensitivity.ValueChanged += (_,_)=>{profile.Scale[index]=Math.CopySign(sensitivity.Value,profile.Scale[index]);label.Text="Sensitivity: "+sensitivity.Value.ToString("0.00");dirty=true;};
            row.Children.Add(label);row.Children.Add(sensitivity);rows.Children.Add(row);
        }
        var footer = new StackPanel();Grid.SetRow(footer,2);grid.Children.Add(footer);
        var buttons = new StackPanel { Orientation = Orientation.Horizontal };
        var status = new TextBlock { TextWrapping = TextWrapping.Wrap,Margin = new(0,12,0,0) };
        void Button(string title,Action action){var b=new Button {Content=title,Style=(Style)FindResource("SecondaryButton"),Margin=new(0,0,10,0)};b.Click+=(_,_)=>action();buttons.Children.Add(b);}
        Button("Save MW3 layout",()=>
        {
            try{profile.Enabled=enabled.IsChecked==true;store.Save(profile);dirty=false;status.Text="MW3 layout saved. Changes apply on the next compatible native launch.";}
            catch(Exception ex){status.Text="Layout could not be saved. "+ex.Message;}
        });
        Button("Close",Close);footer.Children.Add(buttons);footer.Children.Add(status);
        Closing += (_,e)=>{if(dirty&&MessageBox.Show(this,"Discard unsaved controller bindings?","Unsaved layout",MessageBoxButton.YesNo)!=MessageBoxResult.Yes)e.Cancel=true;};
    }
}
