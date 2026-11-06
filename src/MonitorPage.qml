import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
ScrollView {
 id:view;clip:true;contentWidth:availableWidth
 property bool dark:false
 property var service
 property var modelState:service ? service.state : ({points:[],events:[],latest:{},now:Date.now(),collecting:false,error:"",enabled:true})
 property double clockNow:Date.now()
 property double anchorNow:clockNow
 property double domainEnd:following ? clockNow : anchorNow
 property double domainStart:domainEnd-86400000
 onFollowingChanged: { if (!following) anchorNow=clockNow }
 property double selectedStart:domainStart+selection.first.value/100*86400000
 property double selectedEnd:domainStart+selection.second.value/100*86400000
 property bool following:true
 property double duration:600000
 property double cursor:0
 property var picked:null
 function tone(a,b){return dark?a:b}
 function timeText(t){return Qt.formatDateTime(new Date(t),"MM-dd hh:mm:ss")}
 function watts(v){return v===null||v===undefined ? "—" : (v>0?"+":"")+Number(v).toFixed(2)+" W"}
 function selectDuration(ms){duration=ms;following=true;selection.first.value=100-ms/864000;selection.second.value=100;cursor=0}
 function updateClock(){clockNow=Date.now();if(following){selection.first.value=100-duration/864000;selection.second.value=100}}
 function pick(t){cursor=t;var nearest=null,d=Infinity;for(var i=0;i<modelState.points.length;i++){var p=modelState.points[i],distance=Math.abs(p.t-t);if(distance<d){nearest=p;d=distance}}picked=t&&d<=75000?nearest:null}
 Component.onCompleted:updateClock()
 Timer { interval:2000;running:view.visible;repeat:true;onTriggered:view.updateClock() }
 Connections { target:view.service;function onChanged(){view.updateClock()} }
 component Caption: Text { color:view.tone("#9db3a6","#61756a");font.family:"Microsoft YaHei UI";font.pixelSize:12;wrapMode:Text.Wrap }
 component Card: Rectangle { radius:18;color:view.tone("#182129","#ffffff");border.color:view.tone("#2a3931","#d6e1d9") }
 ColumnLayout {
  width:view.availableWidth;spacing:12
  RowLayout {
   Layout.fillWidth:true;spacing:12
   Card { Layout.fillWidth:true;implicitHeight:83
    Column { anchors.fill:parent;anchors.margins:15;spacing:5
     Caption{text:"电量"}
     Text { text:view.modelState.latest.soc===undefined||view.modelState.latest.soc===null ? "—" : Number(view.modelState.latest.soc).toFixed(0)+"%";font.pixelSize:25;color:view.tone("#c8efd5","#245d39") }
    }
   }
   Card { Layout.fillWidth:true;implicitHeight:83
    Column { anchors.fill:parent;anchors.margins:15;spacing:5
     Caption{text:"电池功率 · 系统上报"}
     Text { text:view.watts(view.modelState.latest.power);font.pixelSize:25;color:view.tone("#efbf82","#986026") }
    }
   }
   Card { Layout.fillWidth:true;implicitHeight:83
    Column { anchors.fill:parent;anchors.margins:15;spacing:5
     Caption{text:view.modelState.collecting ? "采集中 · "+view.modelState.interval+" 秒" : "采集已暂停"}
     Caption{text:view.modelState.latest.ac===undefined ? "等待首次采样" : view.modelState.latest.ac ? "外接电源在线" : "电池供电";font.pixelSize:16}
     Caption{text:view.modelState.latest.t ? Qt.formatTime(new Date(view.modelState.latest.t),"hh:mm:ss")+" 更新" : ""}
    }
   }
  }
  Caption { Layout.fillWidth:true;text:view.modelState.mock ? "演示模式：模拟曲线，不代表实测。" : "正值 = 充电，负值 = 放电。固件可能误报方向；功率为 0 不能证明物理旁路。" }
  Rectangle { Layout.fillWidth:true;implicitHeight:notice.implicitHeight+20;radius:10;visible:!!view.modelState.error||!!view.modelState.latest.quality;color:view.tone("#382e22","#fff4e5")
   Caption {id:notice;anchors.fill:parent;anchors.margins:10;text:view.modelState.error || ("数据提示："+(view.modelState.latest.quality||""));color:view.tone("#efbf82","#986026")}
  }
  RowLayout { visible:!!view.modelState.error;Caption{text:"故障仅暂停监测，不改变充电限制。"} Button{text:"重试采集";onClicked:view.service.retry()} }
  RowLayout {
   Repeater { model:["10 分钟","1 小时","6 小时","24 小时"]
    Button {required property int index;required property string modelData;text:modelData;flat:true;onClicked:view.selectDuration([600000,3600000,21600000,86400000][index])}
   }
   Item {Layout.fillWidth:true}
   CheckBox {text:"跟随最新";checked:view.following;onClicked:{view.following=checked;if(checked)view.selectDuration(view.selectedEnd-view.selectedStart)}}
  }
  Card { Layout.fillWidth:true;implicitHeight:440
   ColumnLayout {anchors.fill:parent;anchors.margins:14;spacing:4
    Caption{text:"电量 · %";color:view.tone("#99dcb0","#35764b")}
    TrendPlot {objectName:"socPlot";Layout.fillWidth:true;Layout.preferredHeight:125;points:view.modelState.points;events:view.modelState.events;startTime:view.selectedStart;endTime:view.selectedEnd;dark:view.dark;cursorTime:view.cursor;onHovered:function(t){view.pick(t)} }
    Caption{text:"电池功率 · W（历史细线范围为最小值—最大值）";color:view.tone("#efbf82","#986026")}
    TrendPlot {objectName:"powerPlot";Layout.fillWidth:true;Layout.preferredHeight:160;power:true;points:view.modelState.points;events:view.modelState.events;startTime:view.selectedStart;endTime:view.selectedEnd;dark:view.dark;cursorTime:view.cursor;onHovered:function(t){view.pick(t)} }
    Caption {Layout.fillWidth:true;Layout.preferredHeight:47;text:view.cursor ? (view.picked ? view.timeText(view.picked.t)+"  ·  "+(view.picked.soc===null?"—":Number(view.picked.soc).toFixed(1)+"%")+"  ·  "+view.watts(view.picked.power)+(view.picked.aggregate?"  ·  30 秒聚合":"  ·  原始采样")+(view.picked.quality?"\n"+view.picked.quality:"") : "该时段无样本") : "悬停查看同一时刻的数据。虚线表示电源或采样事件；数据中断不连线。"}
   }
  }
  Card {Layout.fillWidth:true;implicitHeight:172
   ColumnLayout {anchors.fill:parent;anchors.margins:14;spacing:2
    Caption{text:view.timeText(view.selectedStart)+" — "+view.timeText(view.selectedEnd);Layout.fillWidth:true}
    TrendPlot {Layout.fillWidth:true;Layout.preferredHeight:35;compact:true;points:view.modelState.points;startTime:view.domainStart;endTime:view.domainEnd;dark:view.dark}
    RangeSlider {id:selection;
     background: Rectangle {
      x:selection.leftPadding;y:selection.topPadding+selection.availableHeight/2-height/2;width:selection.availableWidth;height:5;radius:3;color:view.tone("#34483c","#d5e1d8")
      Rectangle {x:selection.first.position*parent.width;width:(selection.second.position-selection.first.position)*parent.width;height:parent.height;radius:3;color:view.tone("#80bd98","#68a77d")
       MouseArea {x:12;y:-9;width:Math.max(0,parent.width-24);height:23;cursorShape:Qt.SizeHorCursor
        property double pressX:0;property double low:0;property double high:0
        onPressed:function(mouse){pressX=mapToItem(selection,mouse.x,mouse.y).x;low=selection.first.value;high=selection.second.value;view.following=false}
        onPositionChanged:function(mouse){if(pressed){var delta=(mapToItem(selection,mouse.x,mouse.y).x-pressX)/selection.availableWidth*100;var start=Math.max(0,Math.min(100-(high-low),low+delta));selection.first.value=start;selection.second.value=start+high-low;view.cursor=0}}
       }
      }
     }
objectName:"historyRange";Layout.fillWidth:true;from:0;to:100;first.value:100-600000/864000;second.value:100
     first.onMoved:{if(second.value-first.value<0.14)first.value=second.value-0.14;view.following=false;view.cursor=0}
     second.onMoved:{if(second.value-first.value<0.14)second.value=first.value+0.14;view.following=false;view.cursor=0}
    }
    RowLayout {Button{text:"← 平移";flat:true;onClicked:{view.following=false;var delta=Math.min(selection.first.value,(selection.second.value-selection.first.value)/2);selection.first.value-=delta;selection.second.value-=delta}} Item{Layout.fillWidth:true} Caption{text:"两端缩放 / 中间平移 · 最小约 2 分钟"} Item{Layout.fillWidth:true} Button{text:"平移 →";flat:true;onClicked:{view.following=false;var delta=Math.min(100-selection.second.value,(selection.second.value-selection.first.value)/2);selection.second.value+=delta;selection.first.value+=delta}}}
   }
  }
  Caption {Layout.fillWidth:true;text:"仅保留最近 24 小时。10 分钟内保留原始采样，更早按 30 秒聚合；异常、暂停、休眠及退出期间可能留有空白。"}
  Item {Layout.preferredHeight:8}
 }
}
