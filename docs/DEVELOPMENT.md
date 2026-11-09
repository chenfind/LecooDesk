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

## EC电量计实验版

运行 `start-ec-experimental.ps1`。必须先从托盘正常退出安装版，不可同时运行。构建目录为 `dist-ec-experimental/LecooDesk`，启动脚本通过 `--ec-experimental-data=绝对路径` 显式传递实验模式和数据目录；直接运行普通EXE默认仍采用Windows来源。

实验版配置位于 `D:\code\Lecoo\07-runtime\ec-experimental\LecooDesk`，不读取安装版启用偏好，首次默认关闭。历史使用 `power-ec-experimental.sqlite3`，不混入旧Windows功率记录。必须阅读并接受风险提示；固件比例换算未经过外部校准，不能当作适配器或整机功率。正常退出仍尝试恢复原阈值。

EC电流和电压在Qt控制线程取得；后台工作线程只读取Windows并使用已复制的EC样本，避免与阈值操作并发端口访问。每个16位字完整读取两次一致才接受，失败时显示未知。Windows原始功率、质量标志保存在详细日志中供对照，不用旧值填补EC故障。实验模式未就绪时不会偷偷退回Windows功率。

验证：32项测试及模拟界面通过；真实Controller+Monitor独立配置短对照取得限充负值、Windows旧正值，并成功恢复0/0。尚未完成用户交互、长期运行、休眠重启和外部校准。
