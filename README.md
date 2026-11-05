# LecooDesk

面向 Windows 的实验性硬件控制工作台。目前提供特定 Lecoo N155A 的电池充电区间控制，采用独立硬件适配器，为后续灯光、风扇等能力预留扩展边界。后续功能尚未实现。

> **严重警告：本项目属于个人实验性质，未经厂商认证。无法保证有效、稳定或安全，可能导致充电异常、系统崩溃、数据丢失甚至硬件损坏，重启不一定恢复。作者不承担使用造成的损失或责任。请保存工作、备份数据，充分理解风险后谨慎使用。**

## 下载

[Windows 打包版下载](https://github.com/chenfind/LecooDesk/releases/latest/download/LecooDesk-Windows.zip) · [所有版本](https://github.com/chenfind/LecooDesk/releases)

下载链接在首个 Release 发布后可用。程序尚未签名。请完整解压，保留 EXE 旁的 `_internal` 目录。

- `LecooDesk-demo.exe`：模拟硬件，适合先体验界面。
- `LecooDesk.exe`：正式硬件模式，需要管理员权限和本机已有的 inpoutx64 驱动；本项目不安装驱动。
- `LecooDesk-diagnostics.exe`：同样强制模拟硬件，不是实机检测工具。

**当前硬件白名单仅限 N155A / BIOS N155A_00_V1.2_PKID / IT5571-07。其他型号或 BIOS 不应直接使用，也不应通过修改白名单尝试。**

## 功能

- 0–100% 双滑块，开始和停止阈值至少相差 10 个百分点。
- 启用开关默认关闭，记忆区间和启用偏好。
- 明确区分待应用、已保存和当前生效状态。
- 深色、浅色、跟随系统主题；关闭窗口收起到系统托盘。
- 正常退出尝试恢复启动前的阈值；无独立守护进程。
- 可选开机自启，三级日志及自动保留时长。

调整滑块后点击“应用区间”。“区间已存”表示已保存但限制未启用；“区间生效”表示当前会话已应用。退出请选择托盘“恢复原设置并退出”，关闭窗口不会停止限制。异常退出不能保证恢复。

详见 [使用说明](docs/USAGE.md)、[开发与构建](docs/DEVELOPMENT.md)、[测试边界](docs/TESTING.md) 和 [更新记录](CHANGELOG.md)。

第三方许可见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 和 `LICENSES/`。项目尚未选择源码授权许可证；公开可见不代表已授予再分发授权。
