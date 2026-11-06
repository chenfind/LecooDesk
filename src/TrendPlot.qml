import QtQuick
Item {
 id:plot
 property var points:[]
 property var events:[]
 property double startTime:0
 property double endTime:1
 property double cursorTime:0
 property bool dark:false
 property bool power:false
 property bool compact:false
 signal hovered(double timestamp)
 implicitHeight:power ? 190 : 145
 function formatTime(t) { return Qt.formatTime(new Date(t),"hh:mm") }
 onPointsChanged: canvas.requestPaint()
 onEventsChanged: canvas.requestPaint()
 onStartTimeChanged: canvas.requestPaint()
 onEndTimeChanged: canvas.requestPaint()
 onCursorTimeChanged: canvas.requestPaint()
 onDarkChanged: canvas.requestPaint()
 onWidthChanged: canvas.requestPaint()
 onHeightChanged: canvas.requestPaint()
 Canvas {
  id:canvas; anchors.fill:parent
  onPaint: {
   var c=getContext("2d");c.reset()
   var left=plot.compact ? 2 : 43,right=width-10,top=plot.compact ? 3 : 10,bottom=height-(plot.compact ? 3 : 27)
   var span=Math.max(1,plot.endTime-plot.startTime),a=[],limit=5,i,p,v
   for(i=0;i<plot.points.length;i++) {p=plot.points[i];if(p.t>=plot.startTime && p.t<=plot.endTime) {a.push(p);if(plot.power) {limit=Math.max(limit,Math.abs(p.powerMin||0),Math.abs(p.powerMax||0))}}}
   limit=Math.ceil(limit/5)*5
   function x(t){return left+(t-plot.startTime)/span*(right-left)}
   function y(v){return plot.power ? top+(limit-v)/(2*limit)*(bottom-top) : top+(100-v)/100*(bottom-top)}
   if(!plot.compact) {
    c.font="11px 'Microsoft YaHei UI'";c.fillStyle=plot.dark ? "#8ca49a" : "#6b8172"
    var ticks=plot.power ? [-limit,0,limit] : [0,50,100]
    for(i=0;i<ticks.length;i++){v=ticks[i];c.strokeStyle=plot.dark ? "#2e3c35" : "#e4ebe6";c.lineWidth=(plot.power&&v===0)?1.5:1;c.beginPath();c.moveTo(left,y(v));c.lineTo(right,y(v));c.stroke();c.fillText(v+(plot.power?"":"%"),2,y(v)+4)}
    c.fillText(plot.formatTime(plot.startTime),left,bottom+21);c.fillText(plot.formatTime((plot.startTime+plot.endTime)/2),(left+right)/2-16,bottom+21);c.fillText(plot.formatTime(plot.endTime),right-34,bottom+21)
    c.strokeStyle=plot.dark ? "#566b5e" : "#bccdc0";c.setLineDash([3,5])
    for(i=0;i<plot.events.length;i++){p=plot.events[i];if(p.t>=plot.startTime&&p.t<=plot.endTime){c.beginPath();c.moveTo(x(p.t),top);c.lineTo(x(p.t),bottom);c.stroke()}}
    c.setLineDash([])
   }
   var color=plot.power ? (plot.dark?"#efbf82":"#b8752e") : (plot.dark?"#99dcb0":"#4e9c6b")
   if(plot.power){c.strokeStyle=plot.dark?"#67523b":"#ead5b8";c.lineWidth=3;for(i=0;i<a.length;i++){p=a[i];if(p.powerMin!==null&&p.powerMax!==null&&p.aggregate){c.beginPath();c.moveTo(x(p.t),y(p.powerMin));c.lineTo(x(p.t),y(p.powerMax));c.stroke()}}}
   c.strokeStyle=color;c.lineWidth=plot.compact?1.3:2;c.beginPath();var has=false,previous=null,count=0
   for(i=0;i<a.length;i++){p=a[i];v=plot.power?p.power:p.soc;if(v===null||v===undefined){has=false;previous=null;continue}count++
    if(!has||p.gap||previous&&p.t-previous.t>75000){c.moveTo(x(p.t),y(v))}else {if(!plot.power)c.lineTo(x(p.t),y(previous.soc));c.lineTo(x(p.t),y(v))}has=true;previous=p
   }c.stroke()
   for(i=0;i<a.length;i++){p=a[i];v=plot.power?p.power:p.soc;if(v!==null&&v!==undefined&&(a.length<3||plot.power&&p.quality&&p.quality!=="模拟数据")){c.fillStyle=color;c.beginPath();c.arc(x(p.t),y(v),2,0,Math.PI*2);c.fill()}}
   if(!count&&!plot.compact){c.fillStyle=plot.dark?"#8ca49a":"#6b8172";c.fillText("该时间范围暂无有效数据",left+20,(top+bottom)/2)}
   if(!plot.compact&&plot.cursorTime>=plot.startTime&&plot.cursorTime<=plot.endTime){c.strokeStyle=plot.dark?"#b0c7b6":"#718f7a";c.setLineDash([3,3]);c.beginPath();c.moveTo(x(plot.cursorTime),top);c.lineTo(x(plot.cursorTime),bottom);c.stroke();c.setLineDash([])}
  }
 }
 MouseArea { anchors.fill:parent; hoverEnabled:true; enabled:!plot.compact
  onPositionChanged:function(mouse){plot.hovered(plot.startTime+Math.max(0,Math.min(1,(mouse.x-43)/Math.max(1,width-53)))*(plot.endTime-plot.startTime))}
  onExited:plot.hovered(0)
 }
}
