[Setup]
; Info applicazione
AppName=PyAB
AppVersion=1.0.0
AppPublisher=AmMstools
AppPublisherURL=https://github.com/AmMstools
DefaultDirName={autopf}\PyAB
DefaultGroupName=PyAB
OutputDir=installer_output
OutputBaseFilename=PyAB_Setup_1.0.0
Compression=lzma2
SolidCompression=yes
SetupIconFile=Pyab.ico
UninstallDisplayIcon={app}\Pyab.exe
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern

; Permessi (installa senza admin se possibile)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copia tutto il contenuto della cartella Nuitka standalone
Source: "launcher.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Menu Start
Name: "{group}\PyAB"; Filename: "{app}\Pyab.exe"; IconFilename: "{app}\Pyab.exe"
Name: "{group}\Uninstall PyAB"; Filename: "{uninstallexe}"
; Desktop (opzionale)
Name: "{userdesktop}\PyAB"; Filename: "{app}\Pyab.exe"; IconFilename: "{app}\Pyab.exe"; Tasks: desktopicon

[Run]
; Lancia l'app dopo l'installazione (opzionale)
Filename: "{app}\Pyab.exe"; Description: "Launch PyAB"; Flags: nowait postinstall skipifsilent
