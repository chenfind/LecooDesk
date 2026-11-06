import sys,os,pathlib,tempfile,unittest,logging
os.environ['QT_QPA_PLATFORM']='offscreen'
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt,QObject,Signal
from unittest.mock import patch
from PySide6.QtTest import QSignalSpy
import main
from core import Store
from hardware import MockHardware
from settings import choose_log_directory,DEFAULTS
main.MOCK=True
app=QApplication.instance() or QApplication([])
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.tmp.name);self.controllers=[];self.calls=0
 def factory(self):self.calls+=1;return MockHardware()
 def make(self):
  c=main.Controller(data_dir=self.root/'data',install_dir=self.root/'install',hardware_factory=self.factory);self.controllers.append(c);return c
 def tearDown(self):
  for c in self.controllers:
   c.shutdown();logging.getLogger().removeHandler(c.logs.handler);c.logs.handler.close();c.deleteLater()
  app.processEvents();self.tmp.cleanup()
 def test_no_hardware_before_consent_even_when_enabled(self):
  Store(self.root/'data').save('settings.json',{'enabled':True,'low':70,'high':80})
  c=self.make();c.begin();c.refresh();self.assertEqual(self.calls,0);self.assertIsNone(c.hw)
  c.requestExit();self.assertEqual(self.calls,0)
 def test_accept_starts_and_remembers_only_if_checked(self):
  c=self.make();c.acceptRisk(False);self.assertEqual(self.calls,1);self.assertFalse(c.cfg['warningDismissed']);self.assertTrue(c.operational)
  d=self.make();self.assertTrue(d.state['warningRequired']);d.acceptRisk(True)
  e=self.make();self.assertFalse(e.state['warningRequired']);e.begin();self.assertTrue(e.operational)
 def test_close_hides_without_restoring_and_exit_restores(self):
  c=self.make();c.acceptRisk(False);c.thresholds(70,80);c.enable(True);hw=c.hw;c.trayAvailable=True
  hide=QSignalSpy(c.hideRequested);exits=QSignalSpy(c.exitRequested)
  c.requestClose();self.assertEqual(hide.count(),1);self.assertEqual(exits.count(),0);self.assertEqual(hw.pair(),[80,70]);self.assertTrue(c.active)
  c.requestExit();self.assertEqual(exits.count(),1);self.assertEqual(hw.pair(),[0,0]);self.assertTrue(c.cfg['enabled'])
 def test_range_persist_failure_restores_previous_and_allows_retry(self):
  c=self.make();c.acceptRisk(False);c.thresholds(70,80);c.enable(True)
  with patch.object(c,'persist',side_effect=OSError('disk full')):c.thresholds(60,90)
  self.assertEqual((c.cfg['low'],c.cfg['high']),(70,80));self.assertEqual(c.hw.pair(),[80,70]);self.assertTrue(c.state['rangeSaveFailed'])
  c.thresholds(60,90);self.assertFalse(c.state['rangeSaveFailed']);self.assertEqual(c.hw.pair(),[90,60])
 def test_monitor_settings_remember_without_hardware_before_consent(self):
  c=self.make();c.monitoringOptions(False,False);self.assertFalse(c.cfg['monitorEnabled']);self.assertFalse(c.monitor.allowed)
  d=self.make();self.assertFalse(d.cfg['monitorEnabled']);self.assertFalse(d.cfg['monitorBackground']);d.begin();self.assertIsNone(d.monitor.future);self.assertIsNone(d.monitor.history)
  d.acceptRisk(False);self.assertFalse(d.monitor.active());self.assertIsNotNone(d.monitor.history)
 def test_no_tray_does_not_hide(self):
  c=self.make();c.acceptRisk(False);hide=QSignalSpy(c.hideRequested);c.requestClose();self.assertEqual(hide.count(),0);self.assertIn('托盘',c.error)
 def test_theme_persistence_and_follow_system(self):
  c=self.make();self.assertEqual(c.cfg['theme'],'system');c.setTheme('dark');self.assertTrue(c.state['effectiveDark']);c.setTheme('light');self.assertFalse(c.state['effectiveDark']);d=self.make();self.assertEqual(d.cfg['theme'],'light')
  c.setTheme('system')
  with patch('main.system_dark',return_value=True):
   app.styleHints().colorSchemeChanged.emit(Qt.ColorScheme.Dark);self.assertTrue(c.state['effectiveDark'])
  with patch('main.system_dark',return_value=False):
   app.styleHints().colorSchemeChanged.emit(Qt.ColorScheme.Light);self.assertFalse(c.state['effectiveDark'])
 def test_default_logs_and_existing_choice(self):
  c=self.make();self.assertEqual(c.cfg['logLevel'],2);self.assertEqual(c.logs.root,self.root/'install'/'logs-demo');c.loggingOptions(1,48);d=self.make();self.assertEqual(d.cfg['logLevel'],1);self.assertEqual(d.cfg['hours'],48)
 def test_log_fallback(self):
  blocked=self.root/'not-directory';blocked.write_text('x');path,notice=choose_log_directory(blocked,self.root/'fallback');self.assertEqual(path,self.root/'fallback'/'logs');self.assertIn('回退',notice)
 def test_tray_menu_hides_shows_and_restores(self):
  import tray
  class Icon(QObject):
   activated=Signal(object)
   Trigger=1;DoubleClick=2
   @staticmethod
   def isSystemTrayAvailable():return True
   def __init__(self,*args):super().__init__();self.visible=False;self.notifications=0
   def setContextMenu(self,m):self.menu=m
   def show(self):self.visible=True
   def hide(self):self.visible=False
   def setToolTip(self,t):self.tooltip=t
   def showMessage(self,*args):self.notifications+=1
  class Window:
   visible=True
   def hide(self):self.visible=False
   def showNormal(self):self.visible=True
   def raise_(self):pass
   def requestActivate(self):pass
  class App:
   exits=0
   def quit(self):self.exits+=1
  c=self.make();c.acceptRisk(False);c.thresholds(70,80);c.enable(True);hw=c.hw;window=Window();a=App()
  with patch('tray.QSystemTrayIcon',Icon):
   t=tray.TrayManager(a,window,c,self.root/'icon.ico')
   c.requestClose();self.assertFalse(window.visible);self.assertTrue(c.active);self.assertEqual(t.icon.notifications,1)
   c.requestClose();self.assertEqual(t.icon.notifications,1)
   t.activated(Icon.Trigger);self.assertTrue(window.visible)
   self.assertEqual(t.menu.actions()[-1].text(),'恢复原设置并退出')
   t.menu.actions()[-1].trigger();self.assertEqual(a.exits,1);self.assertFalse(t.icon.visible);self.assertEqual(hw.pair(),[0,0])
if __name__=='__main__':unittest.main()

