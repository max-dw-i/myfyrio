//css_ref Wix_bin\SDK\Microsoft.Deployment.WindowsInstaller.dll;
using Microsoft.Deployment.WindowsInstaller;
using Microsoft.Win32;
using System;
using System.Windows.Forms;
using WixSharp;

class Script
{
    static public void Main()
    {

        var name = "Myfyrio";
        var version = "0.4.1";

        var project = new Project(
            name,

            new Dir(
                @"%ProgramFiles%\" + name,
                new Files(@"Files\*.*"),
                new ExeFileShortcut(
                    name,
                    "[INSTALLDIR]" + name + ".exe",
                    arguments: "-u"
                ),
                new ExeFileShortcut(
                    "Uninstall",
                    "[System64Folder]msiexec.exe",
                    "/x [ProductCode]"
                )
            ),

            new Dir(
                @"%ProgramMenu%\" + name,
                new ExeFileShortcut(
                    name,
                    "[INSTALLDIR]" + name + ".exe",
                    arguments: "-u"
                ),
                new ExeFileShortcut(
                    "Uninstall",
                    "[System64Folder]msiexec.exe",
                    "/x [ProductCode]"
                )
            ),

            new Dir(
                @"%Desktop%",
                new ExeFileShortcut(
                    name,
                    "[INSTALLDIR]" + name + ".exe",
                    arguments: "-u"
                )
            ),

            new ManagedAction(
                CustomActions.CheckMSVCInstalled,
                Return.ignore,
                When.Before,
                Step.LaunchConditions,
                Condition.NOT_Installed,
                Sequence.InstallUISequence
            )
        );

        project.GUID = new Guid("57565fd4-3462-4a22-8196-1cc328c8a3b1");
        project.Version = new Version(version);

        var lowercase_name = name.ToLowerInvariant();
        var url_prefix = "https://github.com/oratosquilla-oratoria/" + lowercase_name + "/";

        project.ControlPanelInfo.Readme = url_prefix;
        project.ControlPanelInfo.HelpLink = url_prefix + "issues";
        project.ControlPanelInfo.UrlInfoAbout = url_prefix;
        project.ControlPanelInfo.UrlUpdateInfo = url_prefix + "releases";
        //project.ControlPanelInfo.ProductIcon = "app_icon.ico";
        project.ControlPanelInfo.Contact = "maxim.shpak@posteo.uk";
        project.ControlPanelInfo.Manufacturer = "Maxim Shpak";
        project.ControlPanelInfo.InstallLocation = "[INSTALLDIR]";
        project.ControlPanelInfo.NoModify = true;

        project.MajorUpgradeStrategy = MajorUpgradeStrategy.Default;
        string err_msg = "A newer version of the programme is already installed";
        project.MajorUpgradeStrategy.NewerProductInstalledErrorMessage = err_msg;

        project.Platform = Platform.x64;
        project.LicenceFile = @"Files\LICENSES\LICENSE.rtf";

        project.UI = WUI.WixUI_InstallDir; //FeatureTree, Mondo

        Compiler.BuildMsi(project);
    }
}

public static class CustomActions
{
    [CustomAction]
    public static ActionResult CheckMSVCInstalled(Session session)
    {
        string reg_location = @"SOFTWARE\WOW6432Node\Microsoft\VisualStudio"
                              + @"\14.0\VC\Runtimes\x64";
        RegistryKey key = Registry.LocalMachine.OpenSubKey(reg_location);
        if (key == null)
        {

            string rt_url = "https://www.microsoft.com/en-us/download/details.aspx?id=52685";
            string msg = "After installing Myfyrio, you need to install "
                         + "'Microsoft Visual C++ 2015 Redistributable' "
                         + "(or newer). Press 'Yes' if you want to download "
                         + "it now, press 'No' if you want to download it "
                         + "yourself later";
            DialogResult answer = MessageBox.Show(
                msg,
                "Microsoft Visual C++ Runtime",
                MessageBoxButtons.YesNo,
                MessageBoxIcon.Warning,
                MessageBoxDefaultButton.Button1
            );
            if (answer == DialogResult.Yes)
                System.Diagnostics.Process.Start(rt_url);
        }
        return ActionResult.Success;
    }
}
