$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
 $scratch=Join-Path $PSScriptRoot '.build'
 New-Item -ItemType Directory -Path (Join-Path $scratch 'tmp') -Force | Out-Null
 $env:TEMP=Join-Path $scratch 'tmp';$env:TMP=$env:TEMP
 & "$PSScriptRoot\.venv\Scripts\python.exe" -m PyInstaller --noconfirm --workpath "$scratch\pyinstaller" --distpath "$PSScriptRoot\dist" "$PSScriptRoot\LecooDesk.spec"
 if($LASTEXITCODE){throw '构建失败'}
} finally { Pop-Location }
