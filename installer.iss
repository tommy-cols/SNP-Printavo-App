[Setup]
AppName=Printavo Quote Creator
AppVersion=1.0
AppPublisher=Your Company Name
DefaultDirName={autopf}\PrintavoQuoteCreator
DefaultGroupName=Printavo Quote Creator
OutputDir=dist
OutputBaseFilename=PrintavoQuoteCreator-Windows-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\PrintavoQuoteCreator.exe

[Files]
Source: "dist\PrintavoQuoteCreator\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Printavo Quote Creator"; Filename: "{app}\PrintavoQuoteCreator.exe"
Name: "{autodesktop}\Printavo Quote Creator"; Filename: "{app}\PrintavoQuoteCreator.exe"

[Run]
Filename: "{app}\PrintavoQuoteCreator.exe"; Description: "Launch Printavo Quote Creator"; Flags: nowait postinstall skipifsilent