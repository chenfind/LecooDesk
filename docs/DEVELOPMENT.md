# 开发与构建

Windows x64、Python 3.14。以下命令从仓库根目录运行：

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\test.ps1
.\build.ps1
```

`dist/` 是唯一发布输出目录，程序位于 `dist/LecooDesk/`。`.build/` 集中保存 PyInstaller 中间文件、测试截图和临时文件；`.venv/` 是开发依赖环境，三者均不进入 Git。旧版本和私人研究资料不属于源码仓库。

## 代码结构

- `hardware.py`：固定白名单硬件适配器和模拟硬件。
- `core.py`：充电会话、原值快照、恢复记录和日志轮转。
- `settings.py`：默认设置及验证规则。
- `main.py`：Qt状态与应用生命周期。
- `tray.py`：系统托盘交互。
- `Main.qml`：界面、草稿状态及动画。

新增硬件能力应实现独立适配器、支持范围校验、状态快照、读回验证和恢复策略。界面不得开放任意地址写入。模拟测试与真实硬件验证应分开，不能因模拟通过就扩大白名单。

打包保留QtWidgets托盘支持，并排除构建环境误带入的非Qt ICU DLL。不要移除该排除规则。演示和诊断EXE均强制使用模拟硬件。
