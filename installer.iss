#define MyAppName "Jigarzon Launcher"
#ifndef AppVersion
  #define AppVersion "2.0.0"
#endif
#define MyAppExeName "JigarzonLauncher.exe"

[Setup]
AppId={{C4C7E7A1-4A5D-4A1E-9B15-8E41B77A1F00}
AppName={#MyAppName}
AppVersion={#AppVersion}
AppPublisher=Jigarzon
DefaultDirName={localappdata}\Programs\Jigarzon Launcher
DefaultGroupName=Jigarzon Launcher
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=Jigarzon-Setup
SetupIconFile=assets\jigarzon.ico
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

[Files]
Source: "dist\JigarzonLauncher.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Jigarzon Launcher"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Jigarzon Launcher"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Jigarzon Launcher"; Flags: nowait postinstall skipifsilent
