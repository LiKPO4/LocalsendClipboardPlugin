#define MyAppName "LocalSend图片剪贴板插件"
#ifndef AppVersion
  #define AppVersion "1.4.3"
#endif
#define MyAppPublisher "LocalSendClipboardPlugin"
#define MyAppExeName "LocalSendClipboardPlugin.exe"

[Setup]
AppId=LocalSendClipboardPlugin
AppName={#MyAppName}
AppVersion={#AppVersion}
AppPublisher={#MyAppPublisher}
AppMutex=LocalSendClipboardPlugin_SingleInstance_Mutex_v2
DefaultDirName={localappdata}\Programs\LocalSendClipboardPlugin
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=LocalSendClipboardPlugin-Setup-{#AppVersion}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
CloseApplicationsFilter={#MyAppExeName}
RestartApplications=no

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "使用说明.md"; DestDir: "{app}"; Flags: ignoreversion

[InstallDelete]
Type: files; Name: "{autodesktop}\{#MyAppName}.lnk"
Type: files; Name: "{autoprograms}\{#MyAppName}.lnk"

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"; Check: ShouldCreateDesktopShortcut

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
function HadDesktopShortcut: Boolean;
begin
  Result := FileExists(ExpandConstant('{autodesktop}\{#MyAppName}.lnk'));
end;

function ShouldCreateDesktopShortcut: Boolean;
begin
  Result := WizardIsTaskSelected('desktopicon') or HadDesktopShortcut();
end;
