; ─────────────────────────────────────────────────────────────────────────────
;  NETD Calculator  –  Inno Setup installer script
;  Requires Inno Setup 6  (https://jrsoftware.org/isinfo.php)
; ─────────────────────────────────────────────────────────────────────────────

[Setup]
AppName=NETD Calculator
AppVersion=1.0.0
AppPublisher=TIPL
AppPublisherURL=
AppSupportURL=
AppUpdatesURL=

; Install to  C:\Program Files\TIPL\NETD Calculator\
DefaultDirName={autopf}\TIPL\NETD Calculator
DefaultGroupName=TIPL\NETD Calculator

; Output
OutputDir=Output
OutputBaseFilename=NETD_Calculator_Setup
SetupIconFile=assets\logo.ico

; Admin elevation is required during installation
PrivilegesRequired=admin

; Compression
Compression=lzma2/ultra64
SolidCompression=yes

; Appearance
WizardStyle=modern
WizardSmallImageFile=assets\logo.png

; Minimum Windows version: Windows 7
MinVersion=6.1

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; \
    Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; \
    Flags: unchecked

[Files]
; Copy everything PyInstaller produced (exe + _internal/ and all DLLs)
Source: "dist\NETD Calculator\*"; \
    DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start-menu shortcut
Name: "{group}\NETD Calculator";               Filename: "{app}\NETD Calculator.exe"
Name: "{group}\{cm:UninstallProgram,NETD Calculator}"; Filename: "{uninstallexe}"

; Optional desktop shortcut (unchecked by default)
Name: "{autodesktop}\NETD Calculator"; \
    Filename: "{app}\NETD Calculator.exe"; \
    Tasks: desktopicon

[Run]
; Offer to launch the app immediately after installation
Filename: "{app}\NETD Calculator.exe"; \
    Description: "{cm:LaunchProgram,NETD Calculator}"; \
    Flags: nowait postinstall skipifsilent
