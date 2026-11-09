#define MyAppName "JLauncher"
#ifndef AppVersion
  #define AppVersion "3.0.0"
#endif
#define MyAppExeName "JLauncher.exe"

[Setup]
AppId={{C4C7E7A1-4A5D-4A1E-9B15-8E41B77A1F00}
AppName={#MyAppName}
AppVersion={#AppVersion}
AppPublisher=JLauncher
DefaultDirName={localappdata}\Programs\JLauncher
UsePreviousAppDir=no
DefaultGroupName=JLauncher
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=JLauncher-Setup-Windows
SetupIconFile=assets\jlauncher.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=yes
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[InstallDelete]
; Remove the previous Jigarzon program folder and Start Menu group on upgrade.
Type: filesandordirs; Name: "{localappdata}\Programs\Jigarzon Launcher"
Type: filesandordirs; Name: "{userprograms}\Jigarzon Launcher"

[Files]
Source: "dist\JLauncher.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\JLauncher"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\JLauncher"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch JLauncher"; Flags: nowait postinstall skipifsilent
