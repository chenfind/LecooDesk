$ErrorActionPreference='Stop'
$src=Join-Path $PSScriptRoot 'dist\LecooDesk'
$dest=Join-Path $env:ProgramFiles 'LecooDesk'
if(-not(Test-Path -LiteralPath (Join-Path $src 'LecooDesk.exe'))){throw '请先构建或将安装脚本放在包含 dist 的源码目录'}
if(Get-Process LecooDesk -ErrorAction SilentlyContinue){throw '请先正常退出 LecooDesk，确认恢复成功'}
New-Item -ItemType Directory -Path $dest -Force | Out-Null
Copy-Item -Path (Join-Path $src '*') -Destination $dest -Recurse -Force
$w=New-Object -ComObject WScript.Shell
$link=$w.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'LecooDesk.lnk'))
$link.TargetPath=Join-Path $dest 'LecooDesk.exe';$link.WorkingDirectory=$dest;$link.Save()
Write-Output "已安装到 $dest；未启动程序，未注册开机任务。"

