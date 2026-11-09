$ErrorActionPreference='Stop'
if(Get-Process -Name LecooDesk,LecooDesk-demo,LecooDesk-diagnostics -ErrorAction SilentlyContinue){throw '请先从托盘正常退出其他 LecooDesk，避免端口冲突。'}
& "$PSScriptRoot\dist-ec-experimental\LecooDesk\LecooDesk.exe" '--ec-experimental-data=D:\code\Lecoo\07-runtime\ec-experimental'
