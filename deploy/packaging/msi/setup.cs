/*MIT License

Copyright (c) 2020 Maxim Shpak <maxim.shpak@posteo.uk>

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom
the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.*/

//css_ref C:\WixSharp\Wix_bin\SDK\Microsoft.Deployment.WindowsInstaller.dll;

using Microsoft.Deployment.WindowsInstaller;
using Microsoft.Win32;
using System;
using System.Collections.Generic;
using System.Windows.Forms;
using WixSharp;
using WixSharp.Controls;

class Script
{
    static public Dictionary<String, String> metadata = ReadMetadata();

    static public void Main()
    {

        Project project = new Project(
            metadata["NAME"],

            new Dir(
                @"%ProgramFiles%\" + metadata["NAME"],
                new Files(@"Files\*.*"),
                new ExeFileShortcut(
                    metadata["NAME"],
                    "[INSTALLDIR]" + metadata["L_NAME"] + ".exe",
                    arguments: "-u"
                ),
                new ExeFileShortcut(
                    "Uninstall",
                    "[System64Folder]msiexec.exe",
                    "/x [ProductCode]"
                )
            ),

            new Dir(
                @"%ProgramMenu%\" + metadata["NAME"],
                new ExeFileShortcut(
                    metadata["NAME"],
                    "[INSTALLDIR]" + metadata["L_NAME"] + ".exe",
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
                    metadata["NAME"],
                    "[INSTALLDIR]" + metadata["L_NAME"] + ".exe",
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
        project.Version = new Version(metadata["VERSION"]);

        project.ControlPanelInfo.HelpLink = metadata["URL_BUG_REPORTS"];
        project.ControlPanelInfo.Readme = metadata["URL_ABOUT"];
        project.ControlPanelInfo.UrlInfoAbout = metadata["URL_ABOUT"];
        project.ControlPanelInfo.UrlUpdateInfo = metadata["URL_RELEASES"];
        //project.ControlPanelInfo.ProductIcon = "app_icon.ico";
        project.ControlPanelInfo.Contact = metadata["AUTHOR_EMAIL"];
        project.ControlPanelInfo.Manufacturer = metadata["AUTHOR"];
        project.ControlPanelInfo.InstallLocation = "[INSTALLDIR]";
        project.ControlPanelInfo.NoModify = true;

        project.MajorUpgradeStrategy = MajorUpgradeStrategy.Default;
        string err_msg = "A newer version of the programme is already installed";
        project.MajorUpgradeStrategy.NewerProductInstalledErrorMessage = err_msg;

        project.Platform = Platform.x64;

        project.UI = WUI.WixUI_InstallDir;
        project.CustomUI = new DialogSequence().On(
            NativeDialogs.WelcomeDlg,
            Buttons.Next,
            new ShowDialog(NativeDialogs.InstallDirDlg)
        ).On(
            NativeDialogs.InstallDirDlg,
            Buttons.Back,
            new ShowDialog(NativeDialogs.WelcomeDlg)
        );

        Compiler.BuildMsi(project);

    }

    static Dictionary<String, String> ReadMetadata()
    {
        Dictionary<String, String> metadata = new Dictionary<String, String>();
        string prefix;
        string[] parts;
        string value;

        char sep = '=';
        char[] shell = {' ', '\n', '\r', '\''};
        string[] metadata_fields = { "NAME", "VERSION", "URL_ABOUT",
                                     "URL_BUG_REPORTS", "URL_RELEASES",
                                     "AUTHOR", "AUTHOR_EMAIL"};

        string[] lines = System.IO.File.ReadAllLines("..\\..\\myfyrio\\metadata.py");

        foreach (string line in lines)
        {
            foreach (string field in metadata_fields)
            {
                prefix = field + ' ' + sep + ' ';
                if (line.StartsWith(prefix))
                {
                    parts = line.Split(sep);
                    value = parts[1].Trim(shell);
                    metadata.Add(field, value);
                }
            }
        }

        metadata.Add("L_NAME", metadata["NAME"].ToLowerInvariant());

        return metadata;
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
            string msg = "After installing the programme, you need to install"
                         + " 'Microsoft Visual C++ 2015 Redistributable'"
                         + " (or newer). Press 'Yes' if you want to download"
                         + " it now, press 'No' if you want to download it"
                         + " yourself later";
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
