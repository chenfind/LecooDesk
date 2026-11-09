import sys,pathlib,os,tempfile,math,time
root=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'));sys.argv=['main.py','--mock'];os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtCore import QObject,QUrl,qInstallMessageHandler,QPointF,Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtQml import QQmlApplicationEngine,QQmlProperty
from PySide6.QtTest import QTest
import main
main.MOCK=True
errors=[]
def message(t,c,m):
 print(m,flush=True)
 if 'Error' in m or 'failed' in m or 'Unexpected' in m:errors.append(m)
qInstallMessageHandler(message)
QQuickStyle.setStyle('Basic');app=QApplication(sys.argv);main.style(app)
qa=root/'.build'/'qa'/'ui';qa.mkdir(parents=True,exist_ok=True)
data=qa/'data';install=qa/'install'
# Fresh risk gate each run without touching real user settings.
if (data/'settings.json').exists():(data/'settings.json').unlink()
c=main.Controller(data_dir=data,install_dir=install,hardware_factory=main.MockHardware)
e=QQmlApplicationEngine();e.rootContext().setContextProperty('backend',c);e.rootContext().setContextProperty('powerMonitor',c.monitor);e.load(QUrl.fromLocalFile(str(root/'src'/'Main.qml')))
assert e.rootObjects(),'QML load failed'
w=e.rootObjects()[0];QTest.qWait(300)
assert c.hw is None and c.state['warningRequired']
assert w.grabWindow().save(str(qa/'warning.png'))
c.acceptRisk(False);assert c.operational
c.thresholds(70,80);c.enable(True);assert c.active and c.hw.pair()==[80,70];c.enable(False);assert c.hw.pair()==[0,0]
slider=w.findChild(QObject,'thresholdRange');level=w.findChild(QObject,'logLevel');hours=w.findChild(QObject,'retentionHours')
assert slider is not None and level is not None and hours is not None
button=w.findChild(QObject,'applyRange');status=w.findChild(QObject,'rangeStatus')
app.processEvents();assert button.property('text')=='区间已存' and not button.property('enabled')
QQmlProperty.write(slider,'first.value',60);QQmlProperty.write(slider,'second.value',90);level.setProperty('currentIndex',1);hours.setProperty('value',100)
c.refresh();app.processEvents()
assert QQmlProperty.read(slider,'first.value')==60 and QQmlProperty.read(slider,'second.value')==90
assert level.property('currentIndex')==1 and hours.property('value')==100
assert button.property('enabled') and button.property('text')=='应用区间'
button.clicked.emit();app.processEvents()
assert (c.cfg['low'],c.cfg['high'])==(60,90) and not button.property('enabled')
c.enable(True);app.processEvents();assert button.property('text')=='区间生效'
QQmlProperty.write(slider,'first.value',65);app.processEvents()
assert button.property('enabled') and '60%–90%' in status.property('text')
c.enable(False)
# Drag the left handle into the right one. Its edge stops at the legal gap.
left=slider.findChild(QObject,'leftRangeHandle');right=slider.findChild(QObject,'rightRangeHandle')
assert abs(left.y()-right.y())<0.01
pos=left.mapToScene(QPointF(left.width()/2,left.height()/2)).toPoint()
QTest.mousePress(w,Qt.LeftButton,Qt.NoModifier,pos)
target=right.mapToScene(QPointF(right.width()/2,right.height()/2)).toPoint()
QTest.mouseMove(w,target)
QTest.mouseRelease(w,Qt.LeftButton,Qt.NoModifier,target)
assert QQmlProperty.read(slider,'first.value')==80 and QQmlProperty.read(slider,'second.value')==90, (QQmlProperty.read(slider,'first.value'),QQmlProperty.read(slider,'second.value'),pos,left.x(),right.x())
assert left.x()+left.width()<=right.x()+0.01
QQmlProperty.write(slider,'first.value',70);QQmlProperty.write(slider,'second.value',80);level.setProperty('currentIndex',2);hours.setProperty('value',72)
for theme in ('light','dark'):
 c.setTheme(theme)
 for page in range(4):
  w.setProperty('page',page);QTest.qWait(300);assert w.grabWindow().save(str(qa/(theme+'-'+str(page)+'.png')))
# Representative history fixture; all data is explicitly simulated.
c.monitor.timer.stop()
now=time.time();history=c.monitor.history
with history.db:
 history.db.execute('DELETE FROM points');history.db.execute('DELETE FROM events')
for i in range(1440):
 if 900<=i<920:continue
 t=now-86400+i*60
 history.add(t,'fixture-a' if i<900 else 'fixture-b',dict(soc=65+12*math.sin(i/110),power=18*math.sin(i/40),ac=(i//180)%2==0,quality='模拟数据'))
history.maintain(now);c.monitor.points=history.rows(now);c.monitor.event_rows=history.events(now);c.monitor.changed.emit()
for theme in ('light','dark'):
 c.setTheme(theme);w.setProperty('page',1);QTest.qWait(200)
 page=w.findChild(QObject,'monitorPage');assert page is not None
 history_slider=w.findChild(QObject,'historyRange')
 history_slider.setValues(99.86,100)
 lo=history_slider.findChild(QObject,'leftRangeHandle');hi=history_slider.findChild(QObject,'rightRangeHandle')
 assert abs(lo.y()-hi.y())<0.01 and lo.x()+lo.width()<=hi.x()+0.01
 page.selectDuration(86400000);w.resize(980,1100);QTest.qWait(250)
 assert w.grabWindow().save(str(qa/(theme+'-monitor-history.png')))
 assert w.findChild(QObject,'socPlot') is not None and w.findChild(QObject,'powerPlot') is not None
 w.resize(980,760);QTest.qWait(100)
 before=page.property('selectedStart');page.setProperty('following',False);page.updateClock();app.processEvents();assert page.property('selectedStart')==before
 c.monitor.setVisible(False);assert c.monitor.interval()==30
 c.monitor.setVisible(True);assert c.monitor.interval()==2
c.monitor.configure(False,True,True);assert not c.monitor.active()

c.setTheme('system');c.trayAvailable=True
c.thresholds(70,80);c.enable(True);hw=c.hw
assert w.close()==False and c.active and hw.pair()==[80,70]
assert c.shutdown() and hw.pair()==[0,0]
assert not errors,errors
print('PASS: warning gate, 10% range, light/dark pages, draft retention and close-to-tray semantics; mock hardware only')
