import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ApplicationWindow {
 id: win; width: 980; height: 760; minimumWidth: 820; minimumHeight: 700; visible: true
 title: "LecooDesk · 电源工作台"; color: win.tone("#0d1319","#f3f7f4")
 property var s: backend ? backend.state : ({soc:0,low:65,high:80,enabled:false,active:false,ready:false,error:"",mock:true,logLevel:2,hours:72,startup:false,effectiveDark:false,warningRequired:true,warningText:""})
 property bool dark: s.effectiveDark === true
 function tone(a,b) { return dark ? a : b }
 property bool rangeDirty: Math.round(range.first.value) !== s.low || Math.round(range.second.value) !== s.high
 property string rangeHint: rangeDirty ? (s.active ? "当前生效："+s.low+"%–"+s.high+"%；新范围待应用" : "新范围待保存；当前未启用限制") : (s.active ? "当前生效："+s.low+"%–"+s.high+"%" : "设置已保存；启用限制后生效")
 property int page: 0
 property int savedLow: -1
 property int savedHigh: -1
 property int savedLog: -1
 property int savedHours: -1
 function syncSettings() {
  if (savedLow !== s.low || savedHigh !== s.high) { range.first.value = s.low; range.second.value = s.high; savedLow = s.low; savedHigh = s.high }
  if (savedLog !== s.logLevel) { level.currentIndex = s.logLevel; savedLog = s.logLevel }
  if (savedHours !== s.hours) { retention.value = s.hours; savedHours = s.hours }
 }
 Component.onCompleted: syncSettings()
 Connections { target: backend; function onChanged() { win.syncSettings() } }
 font.family: "Microsoft YaHei UI"
 onClosing: function(close) { close.accepted = false; backend.requestClose() }
 component LabelText: Text { color: win.tone("#e6ecef","#1b2b22"); font.pixelSize: 14 }
 component ActionButton: Button {
  id:action; implicitHeight:40; implicitWidth:Math.max(100,label.implicitWidth+28)
  contentItem: Text { id:label; text:action.text; color:action.enabled ? win.tone("#c9f4da","#245d39") : win.tone("#6b8278","#8b9e91"); font:action.font; horizontalAlignment:Text.AlignHCenter; verticalAlignment:Text.AlignVCenter }
  background: Rectangle { radius:10; color:action.down ? win.tone("#376449","#b9ddc6") : action.hovered ? win.tone("#31573f","#c7e5d2") : win.tone("#254633","#ddf0e4"); border.color:win.tone("#3a634a","#a3c9b0"); Behavior on color { ColorAnimation { duration:150 } } }
 }
 component Toggle: Switch {
  id:toggle; implicitWidth:52; implicitHeight:32
  indicator: Rectangle { implicitWidth:48; implicitHeight:26; x:2; y:(toggle.height-height)/2; radius:13; color:toggle.checked ? win.tone("#8fd9ac","#4d9c6a") : win.tone("#36454e","#c3cfc8"); Behavior on color { ColorAnimation { duration:180 } }
   Rectangle { width:20; height:20; radius:10; y:3; x:toggle.checked ? 25 : 3; color:toggle.checked ? win.tone("#183225","#ffffff") : win.tone("#abb9c0","#ffffff"); Behavior on x { NumberAnimation { duration:180; easing.type:Easing.OutCubic } } }
  }
 }
 component Panel: Rectangle { Behavior on color { ColorAnimation { duration:180 } } color: win.tone("#182129","#ffffff"); radius: 22; border.color: win.tone("#26333d","#d6e1d9") }
 RowLayout {
  anchors.fill: parent; anchors.margins: 28; spacing: 28
  ColumnLayout {
   Layout.preferredWidth: 180; Layout.maximumWidth: 180; Layout.minimumWidth: 180; Layout.fillHeight: true; spacing: 12
   LabelText { text: "LecooDesk"; font.pixelSize: 23; font.bold: true; color: win.tone("#b5e7cc","#245d39") }
   LabelText { text: "DEVICE STUDIO / 0.2.1"; color: win.tone("#677e8b","#718278"); font.pixelSize: 10; Layout.bottomMargin: 38 }
   Repeater {
    model: ["电池与充电", "偏好设置", "使用说明"]
    delegate: Rectangle {
     required property int index; required property string modelData
     Layout.fillWidth:true; height:48; radius:12
     color:win.page === index ? win.tone("#20372d","#e0eee5") : win.tone("#0d1319","#f3f7f4")
     Behavior on color { ColorAnimation { duration:240; easing.type:Easing.InOutQuad } }
     Rectangle {
      anchors.fill:parent; radius:parent.radius
      color:win.tone("#b9dfc7","#3e8058")
      opacity:nav.containsMouse && win.page !== index ? 0.045 : 0
      Behavior on opacity { NumberAnimation { duration:260; easing.type:Easing.OutCubic } }
     }
     LabelText { anchors.centerIn: parent; text: modelData; color: win.page === index ? win.tone("#c7f6dc","#245d39") : win.tone("#8fa3ae","#62766a") }
     MouseArea { id: nav; anchors.fill: parent; hoverEnabled: true; onClicked: win.page = index }
    }
   }
   Item { Layout.fillHeight: true }
   ActionButton { text: "恢复并退出"; onClicked: backend.requestExit() }
   LabelText { text: s.mock ? "● 演示模式 / 无硬件写入" : "● N155A · IT5571-07"; font.pixelSize: 11; color: win.tone("#85a594","#51795f") }
   LabelText { text: "本地运行 · 无遥测"; font.pixelSize: 11; color: win.tone("#637780","#718278") }
  }
  ColumnLayout {
   Layout.fillWidth: true; Layout.fillHeight: true; spacing: 18
   LabelText { text: page === 0 ? "让电池，保持从容。" : page === 1 ? "按你的习惯运行。" : "了解运行边界。"; font.pixelSize: 29; font.bold: true; Layout.topMargin: 10 }
   LabelText { text: page === 0 ? "为长期插电工作，留一点余量。" : "所有设置保存在这台电脑上。"; color: win.tone("#8299a5","#61756a"); Layout.bottomMargin: 10 }
   StackLayout {
    id: pages; currentIndex: page; Layout.fillWidth: true; Layout.fillHeight: true
    onCurrentIndexChanged: pageFade.restart()
    NumberAnimation { id: pageFade; target: pages; property: "opacity"; from: 0.94; to: 1; duration: 180; easing.type: Easing.OutCubic }
    ColumnLayout {
     spacing: 18
     Panel {
      Layout.fillWidth: true; Layout.preferredHeight: 170
      RowLayout {
       anchors.fill: parent; anchors.margins: 26
       ColumnLayout {
        LabelText { text: "当前电量"; color: win.tone("#90a8b3","#61756a") }
        LabelText { text: s.soc + "%"; font.pixelSize: 52; font.bold: true }
        LabelText { text: s.active ? "限制已生效 · 阈值已读回校验" : s.enabled ? "期望已启用 · 当前未生效" : "限制未启用 · 使用系统默认充电策略"; color: s.active ? win.tone("#9ee5ba","#296f43") : win.tone("#92a4af","#61756a") }
       }
       Item { Layout.fillWidth: true }
       Rectangle {
        width: 150; height: 70; radius: 18; color: win.tone("#243b32","#e0efe5"); border.color: win.tone("#74c697","#5ca878"); border.width: 2
        Rectangle { anchors.left: parent.left; anchors.leftMargin: 7; anchors.verticalCenter: parent.verticalCenter; height: 56; radius: 12; width: Math.max(0,136 * s.soc / 100); color: win.tone("#9cdeb8","#72bb8b"); Behavior on width { NumberAnimation { duration: 700; easing.type: Easing.OutCubic } } }
       }
      }
     }
     Panel {
      Layout.fillWidth: true; Layout.preferredHeight: 285
      ColumnLayout {
       anchors.fill: parent; anchors.margins: 26; spacing: 12
       RowLayout {
        LabelText { text: "充电区间"; font.pixelSize: 20; font.bold: true; Layout.fillWidth: true }
        Toggle { checked: s.enabled; enabled: s.ready; onClicked: { if (checked) backend.activate(Math.round(range.first.value),Math.round(range.second.value)); else backend.enable(false) } }
       }
       RowLayout {
        LabelText { text: "开始充电  " + Math.round(range.first.value) + "%"; color: win.tone("#a7dfbd","#296f43"); Layout.fillWidth: true }
        LabelText { text: "停止充电  " + Math.round(range.second.value) + "%"; color: win.tone("#a7dfbd","#296f43") }
       }
       RangeSlider {
        id: range; objectName: "thresholdRange"; Layout.fillWidth: true; from: 0; to: 100; stepSize: 1
                first.value: 65; second.value: 80; snapMode: RangeSlider.SnapAlways
        implicitHeight:40
        background: Rectangle { x:range.leftPadding; y:range.topPadding+range.availableHeight/2-height/2; width:range.availableWidth; height:5; radius:3; color:win.tone("#33434d","#c9d8ce")
         Rectangle { x:range.first.position*parent.width; width:(range.second.position-range.first.position)*parent.width; height:parent.height; radius:3; color:win.tone("#a6e3bf","#5ba475") }
        }
        first.handle: Rectangle { x:range.leftPadding+range.first.visualPosition*(range.availableWidth-width); y:range.topPadding+range.availableHeight/2-height/2; implicitWidth:24; implicitHeight:24; radius:12; color:win.tone("#d0f3dc","#ffffff"); border.width:range.first.pressed ? 4 : 2; border.color:win.tone("#5a9e74","#4a9563"); scale:range.first.pressed ? 1.15 : 1; Behavior on scale { NumberAnimation { duration:120 } } }
        second.handle: Rectangle { x:range.leftPadding+range.second.visualPosition*(range.availableWidth-width); y:range.topPadding+range.availableHeight/2-height/2; implicitWidth:24; implicitHeight:24; radius:12; color:win.tone("#d0f3dc","#ffffff"); border.width:range.second.pressed ? 4 : 2; border.color:win.tone("#5a9e74","#4a9563"); scale:range.second.pressed ? 1.15 : 1; Behavior on scale { NumberAnimation { duration:120 } } }
        first.onMoved: { if (second.value - first.value < 10) first.value = second.value - 10 }
        second.onMoved: { if (second.value - first.value < 10) second.value = first.value + 10 }
       }
       RowLayout {
        LabelText { text: "0%"; color: win.tone("#657c88","#718278"); Layout.fillWidth: true }
        LabelText { text: "100%"; color: win.tone("#657c88","#718278") }
       }
       RowLayout {
        LabelText { objectName:"rangeStatus"; text:win.rangeHint; wrapMode:Text.Wrap; color: win.tone("#8397a3","#61756a"); Layout.fillWidth: true; font.pixelSize: 12 }
        ActionButton { objectName:"applyRange"; Layout.minimumWidth:112; Layout.maximumWidth:112; Layout.preferredWidth:112
         text:win.rangeDirty || s.rangeSaveFailed ? "应用区间" : s.active ? "区间生效" : "区间已存"
         enabled:win.rangeDirty || s.rangeSaveFailed
         onClicked: backend.thresholds(Math.round(range.first.value),Math.round(range.second.value)) }
       }
       LabelText { text: "显示电量可能短暂超过设定值约 1%；下限用于停充后的再次充电。"; color: win.tone("#637985","#718278"); font.pixelSize: 11; wrapMode: Text.Wrap; Layout.fillWidth: true }
      }
     }
     Item { Layout.fillHeight: true }
    }
    ScrollView {
     id: settingsScroll; clip:true; contentWidth:availableWidth
     ColumnLayout {
      width:settingsScroll.availableWidth; spacing:18
      Panel {
       Layout.fillWidth:true; Layout.preferredHeight:110
       RowLayout { anchors.fill:parent; anchors.margins:24
        ColumnLayout { LabelText { text:"外观主题"; font.pixelSize:19 } LabelText { text:"跟随系统会自动响应 Windows 外观变化。"; color:win.tone("#8299a5","#61756a"); font.pixelSize:11 } }
        Item { Layout.fillWidth:true }
        ComboBox { objectName:"themeSelector"; model:["跟随系统","浅色","深色"]; currentIndex:s.theme === "dark" ? 2 : s.theme === "light" ? 1 : 0; onActivated: backend.setTheme(["system","light","dark"][currentIndex]) }
       }
      }
      Panel {
       Layout.fillWidth:true; Layout.preferredHeight:135
       ColumnLayout { anchors.fill:parent; anchors.margins:24
        RowLayout { LabelText { text:"登录 Windows 后启动"; font.pixelSize:19; Layout.fillWidth:true } Toggle { checked:s.startup; onClicked:backend.startup(checked) } }
        LabelText { text:"启动后先确认风险，再沿用启用偏好。选择不再提示后自动应用。"; color:win.tone("#8299a5","#61756a"); font.pixelSize:12; wrapMode:Text.Wrap; Layout.fillWidth:true }
       }
      }
      Panel {
       Layout.fillWidth:true; Layout.preferredHeight:340
       ColumnLayout { anchors.fill:parent; anchors.margins:24; spacing:14
        LabelText { text:"诊断日志"; font.pixelSize:20; font.bold:true }
        RowLayout { LabelText { text:"记录级别"; Layout.fillWidth:true } ComboBox { id:level; objectName:"logLevel"; model:["关闭","简单","详细"]; currentIndex:2 } }
        RowLayout { LabelText { text:"仅保留最近（小时）"; Layout.fillWidth:true } SpinBox { id:retention; objectName:"retentionHours"; from:1; to:720; value:72; editable:true } }
        LabelText { text:"保存位置："+s.logPath; color:win.tone("#8299a5","#61756a"); font.pixelSize:11; wrapMode:Text.WrapAnywhere; Layout.fillWidth:true }
        LabelText { visible:!!s.logNotice; text:s.logNotice || ""; color:win.tone("#f3b8ab","#9d2926"); font.pixelSize:11; wrapMode:Text.Wrap; Layout.fillWidth:true }
        RowLayout { ActionButton { text:"打开日志文件夹"; onClicked:backend.openLogs() } Item { Layout.fillWidth:true } ActionButton { text:"保存日志设置"; onClicked:backend.loggingOptions(level.currentIndex,retention.value) } }
        LabelText { text:"默认详细；日志只保存在本机，不自动上传。"; color:win.tone("#728995","#718278"); font.pixelSize:11; Layout.fillWidth:true }
       }
      }
      Item { Layout.preferredHeight:12 }
     }
    }
    ScrollView {
     id:helpScroll; clip:true; contentWidth:availableWidth
     ColumnLayout {
      width:helpScroll.availableWidth; spacing:18
      Rectangle {
       Layout.fillWidth:true; implicitHeight:warningHelp.implicitHeight+56; radius:18; color:win.tone("#412d2d","#fff0ed"); border.width:2; border.color:"#b94a48"
       ColumnLayout { id:warningHelp; anchors.left:parent.left; anchors.right:parent.right; anchors.top:parent.top; anchors.margins:24; spacing:12
        LabelText { text:"严重警告 · 个人实验性软件"; font.pixelSize:21; font.bold:true; color:win.tone("#f3b8ab","#9d2926") }
        LabelText { text:s.warningText; wrapMode:Text.Wrap; Layout.fillWidth:true; lineHeight:1.4; color:win.tone("#f3b8ab","#9d2926") }
       }
      }
      Panel {
       Layout.fillWidth:true; implicitHeight:helpContent.implicitHeight+56
       ColumnLayout { id:helpContent; anchors.left:parent.left; anchors.right:parent.right; anchors.top:parent.top; anchors.margins:24; spacing:18
        LabelText { text:"使用与恢复"; font.pixelSize:23; font.bold:true }
        LabelText { Layout.fillWidth:true; wrapMode:Text.Wrap; lineHeight:1.5; text:"启用限制后保存原阈值并校验写入结果。上下限可以相差 10 个百分点。\n\n点击窗口关闭按钮会收起到右下角系统托盘，程序及限制仍在运行。点击托盘图标可重新打开；右键选择“恢复原设置并退出”，或使用左侧“恢复并退出”，才会恢复原设置并结束程序。系统托盘不可用时不会隐藏窗口。\n\n启用偏好会被记忆。异常结束可能留下限制；下次启动在风险确认之后尝试恢复上次记录，再按偏好应用。选择退出警告弹窗不会接触硬件。\n\n日志默认详细，优先保存在 EXE 所在目录的 logs 文件夹；演示版为 logs-demo。目录不可写时会提示回退位置。旧日志不会自动搬迁，新的日志按小时及大小拆分并按保留时长清理。\n\n当前仅支持已验证的 N155A、BIOS V1.2、IT5571-07。程序不安装驱动、不刷写固件；需要现有 inpoutx64 驱动和管理员权限。不要与其他 EC 控制工具同时运行。\n\n开机自启使用当前用户的高权限计划任务。主题默认跟随系统，设置和风险提示偏好仅保存在本机。"; color:win.tone("#a2b3bc","#50695a") }
       }
      }
     }
    }

   }
   Rectangle {
    Layout.fillWidth:true; Layout.preferredHeight: s.error ? errorText.implicitHeight + 28 : 0; visible: !!s.error; radius:12; color:win.tone("#412d2d","#fff0ed")
    LabelText { id:errorText; anchors.fill:parent; anchors.margins:14; text:s.error; color:win.tone("#f3b8ab","#9d2926"); wrapMode:Text.Wrap }
    Behavior on Layout.preferredHeight { NumberAnimation { duration:180 } }
   }
  }
 }
 Dialog {
  id:riskDialog; objectName:"startupRiskDialog"; modal:true; dim:true; closePolicy:Popup.NoAutoClose
  visible:backend && s.warningRequired; anchors.centerIn:parent; width:Math.min(win.width-64,700); padding:26
  background: Rectangle { radius:20; color:win.tone("#241b1e","#fffafa"); border.width:3; border.color:"#b94a48" }
  header: Rectangle { implicitHeight:86; color:"transparent"
   RowLayout { anchors.fill:parent; anchors.margins:26; spacing:16
    Rectangle { width:42; height:42; radius:10; color:"#b94a48"; Text { anchors.centerIn:parent; text:"!"; color:"#ffffff"; font.bold:true; font.pixelSize:32 } }
    ColumnLayout { LabelText { text:"严重警告"; font.bold:true; font.pixelSize:25; color:win.tone("#f3b8ab","#9d2926") } LabelText { text:"继续前，请认真阅读以下风险说明。"; color:win.tone("#8299a5","#61756a"); font.pixelSize:12 } }
   }
  }
  contentItem: ColumnLayout { spacing:20
   LabelText { text:s.warningText; wrapMode:Text.Wrap; Layout.fillWidth:true; font.pixelSize:15; lineHeight:1.55 }
   CheckBox { id:suppressWarning; objectName:"suppressRiskWarning"; text:"我已了解风险，下次启动不再显示" }
  }
  footer: Item { implicitHeight:78
   RowLayout { anchors.fill:parent; anchors.margins:20
    ActionButton { objectName:"declineRisk"; text:"退出软件"; onClicked:backend.requestExit() }
    Item { Layout.fillWidth:true }
    ActionButton { objectName:"acceptRisk"; text:"理解风险，继续使用"; onClicked:backend.acceptRisk(suppressWarning.checked) }
   }
  }
 }

}







