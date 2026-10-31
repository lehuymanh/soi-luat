; Trình cài một file: SoiLuat-Setup.exe (không cần quyền admin, cài cho người dùng hiện tại).
; Build: ISCC /DSrc=<thư mục SoiLuat do build.ps1 tạo> /DOut=<thư mục ra> pack\SoiLuat.iss
#ifndef Src
  #error Thiếu /DSrc=thư mục dist\SoiLuat
#endif
#ifndef Out
  #define Out "."
#endif
#define AppVer "0.9"

[Setup]
AppId={{6F1C2B9E-4A53-4D0B-9C57-5015A1B0C0DE}
AppName=Soi Luật
AppVersion={#AppVer}
AppPublisher=Soi Luật
DefaultDirName={localappdata}\Programs\SoiLuat
DefaultGroupName=Soi Luật
PrivilegesRequired=lowest
OutputDir={#Out}
OutputBaseFilename=SoiLuat-Setup
Compression=lzma2/max
SolidCompression=yes
DiskSpanning=no
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\SoiLuat.exe
DisableProgramGroupPage=yes
WizardStyle=modern

[Languages]
Name: "vi"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "{#Src}\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

; Kho dữ liệu nằm ở %LOCALAPPDATA%\SoiLuat\data (WorkingDir của lối tắt), không nằm trong thư mục cài:
; gỡ hoặc cài lại không mất kho.
[Dirs]
Name: "{localappdata}\SoiLuat"

[Icons]
Name: "{autoprograms}\Soi Luật"; Filename: "{app}\SoiLuat.exe"; WorkingDir: "{localappdata}\SoiLuat"
Name: "{autodesktop}\Soi Luật"; Filename: "{app}\SoiLuat.exe"; WorkingDir: "{localappdata}\SoiLuat"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Tạo biểu tượng ngoài màn hình"; Flags: unchecked

[Run]
Filename: "{app}\SoiLuat.exe"; WorkingDir: "{localappdata}\SoiLuat"; Description: "Mở Soi Luật"; Flags: nowait postinstall skipifsilent
