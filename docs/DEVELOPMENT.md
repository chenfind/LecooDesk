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

## 监测模块

battery_source.py封装Windows电池类QUERY IOCTL和模拟数据源，不访问EC/SMBus。CAPABILITIES为未来适配器及整机功率保留入口，当前标记不可用。monitor.py使用单个后台工作线程执行一次查询，主线程串行接收结果及SQLite事务；停止采集会递增代次并丢弃在途结果。history.py负责有界存储与聚合。MonitorPage.qml与TrendPlot.qml使用QtQuick Canvas绘图，不需要QtCharts额外模块。监测故障独立于充电会话，不应阻止正常恢复阈值。

构建后先完成模拟验收并提交源码，再运行 `.\.venv\Scripts\python.exe package_release.py` 生成发布ZIP、对应HEAD源码ZIP和SHA256SUMS。发布目录包含测试运行日志时，脚本会拒绝打包，须先将日志归档。
