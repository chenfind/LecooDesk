$ErrorActionPreference='Stop'
Push-Location $PSScriptRoot
try {
 New-Item -ItemType Directory -Path '.build\tmp' -Force | Out-Null
 $env:TEMP=Join-Path $PSScriptRoot '.build\tmp';$env:TMP=$env:TEMP
 & '.\.venv\Scripts\python.exe' -m unittest discover -s tests -p 'test_*.py' -v
 if($LASTEXITCODE){throw '单元测试失败'}
 & '.\.venv\Scripts\python.exe' tests\smoke_ui.py
 if($LASTEXITCODE){throw '界面测试失败'}
} finally { Pop-Location }
