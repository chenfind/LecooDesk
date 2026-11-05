import sys,pathlib,os,tempfile
root=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'));sys.argv=['main.py','--mock'];os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtCore import QObject,QUrl,qInstallMessageHandler
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
e=QQmlApplicationEngine();e.rootContext().setContextProperty('backend',c);e.load(QUrl.fromLocalFile(str(root/'src'/'Main.qml')))
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
QQmlProperty.write(slider,'first.value',70);QQmlProperty.write(slider,'second.value',80);level.setProperty('currentIndex',2);hours.setProperty('value',72)
for theme in ('light','dark'):
 c.setTheme(theme)
 for page in range(3):
  w.setProperty('page',page);QTest.qWait(300);assert w.grabWindow().save(str(qa/(theme+'-'+str(page)+'.png')))
c.setTheme('system');c.trayAvailable=True
c.thresholds(70,80);c.enable(True);hw=c.hw
assert w.close()==False and c.active and hw.pair()==[80,70]
assert c.shutdown() and hw.pair()==[0,0]
assert not errors,errors
print('PASS: warning gate, 10% range, light/dark pages, draft retention and close-to-tray semantics; mock hardware only')
