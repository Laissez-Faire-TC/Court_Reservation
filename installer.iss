; Inno Setup Script
; 城北中央公園テニスコート予約 インストーラー

#define AppName "城北中央公園テニスコート予約"
#define AppVersion "1.0"
#define AppPublisher "Laissez-Faire T.C."
#define AppExeName "城北中央公園テニスコート予約.exe"

[Setup]
AppId={{B3F2A1C4-7E9D-4F8A-B2E6-3D1C5A7F9E0B}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir=installer_output
OutputBaseFilename=城北中央公園テニスコート予約_Setup
SetupIconFile=app_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; 日本語UI
ShowLanguageDialog=no

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "デスクトップにショートカットを作成する"; GroupDescription: "追加タスク:"; Flags: unchecked

[Files]
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; 自己署名証明書を使う場合はこの行のコメントを外す
; Source: "LFC_cert.cer"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{#AppName} のアンインストール"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; 自己署名証明書を使う場合はこの行のコメントを外す（信頼されたルート証明機関にインストール）
; Filename: "certutil.exe"; Parameters: "-addstore Root ""{app}\LFC_cert.cer"""; Flags: runhidden
Filename: "{app}\{#AppExeName}"; Description: "{#AppName} を起動する"; Flags: nowait postinstall skipifsilent
