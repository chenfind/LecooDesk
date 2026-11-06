import sys,os,pathlib,logging,subprocess,html
from PySide6.QtCore import QObject,Signal,Slot,Property,QTimer,QUrl,Qt,qInstallMessageHandler,QtMsgType
from PySide6.QtGui import QIcon,QFontDatabase,QPalette,QColor,QGuiApplication
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtNetwork import QLocalServer,QLocalSocket
from hardware import Hardware,MockHardware
from core import Store,Logs,ChargeSession
from settings import DEFAULTS,WARNING_TEXT,validate_settings,valid_range,choose_log_directory
from tray import TrayManager
from monitor import Monitor
MOCK='--mock' in sys.argv or '--smoke' in sys.argv or pathlib.Path(sys.executable).stem.lower() in ('lecoodesk-demo','lecoodesk-diagnostics')
ROOT=pathlib.Path(__file__).resolve().parent
VERSION='0.3.0'

def system_dark():
    app=QGuiApplication.instance()
    if app:
        scheme=app.styleHints().colorScheme()
        if scheme!=Qt.ColorScheme.Unknown:return scheme==Qt.ColorScheme.Dark
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize') as key:
            return winreg.QueryValueEx(key,'AppsUseLightTheme')[0]==0
    except OSError:return False

def apply_palette(app,dark):
    colors=('#0d1319','#e6ecef','#101b22','#294536','#c9f4da','#90d9af','#10251a') if dark else ('#f3f7f4','#1b2b22','#ffffff','#dceddf','#245d39','#4c9a69','#ffffff')
    bg,text,base,button,button_text,accent,accent_text=colors
    p=app.palette()
    for role,color in ((QPalette.Window,bg),(QPalette.WindowText,text),(QPalette.Base,base),(QPalette.Text,text),(QPalette.Button,button),(QPalette.ButtonText,button_text),(QPalette.Highlight,accent),(QPalette.HighlightedText,accent_text)):
        p.setColor(role,QColor(color))
    app.setPalette(p)

def style(app):
    for name in ('msyh.ttc','segoeui.ttf'):
        font=pathlib.Path(os.environ.get('WINDIR',r'C:\Windows'))/'Fonts'/name
        if font.exists():QFontDatabase.addApplicationFont(str(font))
    apply_palette(app,system_dark())

class Controller(QObject):
    changed=Signal()
    showRequested=Signal()
    hideRequested=Signal()
    exitRequested=Signal()
    def __init__(self,data_dir=None,install_dir=None,hardware_factory=None):
        super().__init__()
        base=pathlib.Path(data_dir) if data_dir else pathlib.Path(os.environ.get('LECOODESK_DATA',os.environ.get('LOCALAPPDATA',str(ROOT))))/('LecooDesk-demo' if MOCK else 'LecooDesk')
        self.store=Store(base);self.cfg=dict(DEFAULTS)
        self.error='';self.active=False;self.soc=0;self.temp=0;self.hw=None;self.session=None
        self.range_save_failed=False;self.operational=False;self.accepted=False;self.started=False;self.config_error=False;self.trayAvailable=False
        self._factory=hardware_factory or (MockHardware if MOCK else Hardware)
        app_dir=pathlib.Path(install_dir) if install_dir else (pathlib.Path(sys.executable).parent if getattr(sys,'frozen',False) else ROOT.parent)
        path,self.log_notice=choose_log_directory(app_dir,base,MOCK)
        self.logs=Logs(path)
        try:
            self.cfg.update(self.store.load('settings.json',{}));validate_settings(self.cfg)
        except Exception as e:
            self.error='设置文件无效：'+str(e);self.cfg=dict(DEFAULTS);self.config_error=True
        self.accepted=self.cfg['warningDismissed']
        self.monitor=Monitor(base/'history'/'power.sqlite3',mock=MOCK);self.monitor.setParent(self)
        self.monitor.configure(self.cfg['monitorEnabled'],self.cfg['monitorBackground'],False)
        self.logs.configure(self.cfg['logLevel'],self.cfg['hours'])
        logging.info('startup version=%s mock=%s theme=%s enabled_preference=%s log_path=%s warning_dismissed=%s',VERSION,MOCK,self.cfg['theme'],self.cfg['enabled'],path,self.cfg['warningDismissed'])
        if self.log_notice:logging.warning(self.log_notice)
        if self.error:logging.error(self.error)
        self.timer=QTimer(self);self.timer.timeout.connect(self.refresh);self.timer.start(3000)
        self.house=QTimer(self);self.house.timeout.connect(self.rotate);self.house.start(60000)
        app=QGuiApplication.instance()
        if app:app.styleHints().colorSchemeChanged.connect(self.updateTheme)
        self.updateTheme()
    def fail(self,e):
        self.error=str(e);logging.exception('operation_failed');self.changed.emit()
    def persist(self):self.store.save('settings.json',self.cfg)
    def begin(self):
        if self.accepted:
            self.monitor.configure(self.cfg['monitorEnabled'],self.cfg['monitorBackground'],True)
            self.initializeHardware()
    def initializeHardware(self):
        if not self.accepted or self.started or self.config_error:return
        self.started=True
        try:
            self.hw=self._factory();self.session=ChargeSession(self.hw,self.store)
            self.session.recover();self.operational=True
            if self.cfg['enabled']:
                self.session.enable(self.cfg['low'],self.cfg['high']);self.active=True
            self.refresh()
        except Exception as e:self.fail(e)
        self.changed.emit()
    @Slot(bool)
    def acceptRisk(self,dismiss):
        if self.accepted:return
        try:
            self.cfg['warningDismissed']=bool(dismiss);self.persist()
            self.accepted=True;logging.info('risk_warning_accepted suppress_future=%s',dismiss)
            self.monitor.configure(self.cfg['monitorEnabled'],self.cfg['monitorBackground'],True)
            self.changed.emit();self.initializeHardware()
        except Exception as e:self.fail(e)
    @Property('QVariantMap',notify=changed)
    def state(self):
        dark=self.cfg['theme']=='dark' or self.cfg['theme']=='system' and system_dark()
        return dict(self.cfg,soc=self.soc,temp=self.temp,active=self.active,error=self.error,mock=MOCK,ready=self.operational,logPath=str(self.logs.root),logNotice=self.log_notice,effectiveDark=dark,warningRequired=not self.accepted,warningText=WARNING_TEXT,trayAvailable=self.trayAvailable,version=VERSION,rangeSaveFailed=self.range_save_failed)
    @Slot()
    def updateTheme(self,*args):
        app=QGuiApplication.instance()
        if app:apply_palette(app,self.state['effectiveDark'])
        self.changed.emit()
    @Slot(str)
    def setTheme(self,theme):
        try:
            if theme not in ('system','dark','light'):raise ValueError('无效主题')
            self.cfg['theme']=theme;self.persist();logging.info('theme_changed %s',theme);self.updateTheme()
        except Exception as e:self.fail(e)
    def rotate(self):
        try:
            self.logs.configure(self.cfg['logLevel'],self.cfg['hours'])
            logging.info('status_summary soc=%d active=%s enabled_preference=%s error=%s',self.soc,self.active,self.cfg['enabled'],self.error)
        except Exception as e:self.fail(e)
    def refresh(self):
        try:
            if self.hw:
                snapshot=self.hw.snapshot();self.soc=snapshot['soc'];self.temp=snapshot['temperature']
                if self.active and self.hw.pair()!=self.session.expected:
                    self.error='阈值被外部改变。已暂停自动写入，请停止限制或退出。';self.active=False
                logging.debug('status soc=%d temp=%d active=%s',self.soc,self.temp,self.active)
        except Exception as e:self.fail(e)
        self.changed.emit()
    @Slot(bool)
    def enable(self,v):
        try:
            if not self.accepted or not self.session or not self.operational:raise RuntimeError('尚未确认风险，或硬件未就绪')
            if v:self.session.enable(self.cfg['low'],self.cfg['high'])
            else:self.session.disable()
            self.active=v;self.cfg['enabled']=v;self.error='';self.persist()
        except Exception as e:self.fail(e)
        self.changed.emit()
    @Slot(int,int)
    def activate(self,low,high):
        self.thresholds(low,high)
        if not self.error:self.enable(True)
    @Slot(int,int)
    def thresholds(self,low,high):
        previous=(self.cfg['low'],self.cfg['high'])
        was_active=self.active
        try:
            if not valid_range(low,high):raise ValueError('两个阈值必须相差至少 10 个百分点')
            if self.active:self.session.enable(low,high)
            self.cfg.update(low=low,high=high)
            try:self.persist()
            except Exception:
                self.cfg.update(low=previous[0],high=previous[1])
                if was_active:
                    try:self.session.enable(*previous)
                    except Exception as rollback:
                        self.active=False
                        raise RuntimeError('设置保存失败，且无法恢复此前区间：'+str(rollback))
                raise
            self.range_save_failed=False;self.error=''
        except Exception as e:
            self.range_save_failed=True;self.fail(e)
        self.changed.emit()
    @Slot(int,int)
    def loggingOptions(self,level,hours):
        try:
            if level not in (0,1,2) or not 1<=hours<=720:raise ValueError('日志选项无效')
            self.logs.configure(level,hours);self.cfg.update(logLevel=level,hours=hours);self.persist()
        except Exception as e:self.fail(e)
        self.changed.emit()
    @Slot(bool)
    def startup(self,v):
        try:
            if MOCK:raise RuntimeError('演示模式不修改开机任务')
            if not getattr(sys,'frozen',False):raise RuntimeError('请使用打包后的 EXE 配置自启')
            name='LecooDesk-'+str(os.getlogin())
            if v:
                if not pathlib.Path(sys.executable).is_relative_to(pathlib.Path(os.environ['ProgramFiles'])):raise RuntimeError('请先安装到 Program Files，再启用高权限自启')
                sid=subprocess.check_output(['whoami','/user','/fo','csv','/nh'],text=True,creationflags=0x08000000).strip().split(',')[-1].strip('"')
                exe=html.escape(sys.executable);sid=html.escape(sid)
                xml=f'''<?xml version="1.0" encoding="UTF-16"?><Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task"><Triggers><LogonTrigger><UserId>{sid}</UserId><Delay>PT15S</Delay></LogonTrigger></Triggers><Principals><Principal id="Author"><UserId>{sid}</UserId><LogonType>InteractiveToken</LogonType><RunLevel>HighestAvailable</RunLevel></Principal></Principals><Settings><MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy><DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries><StopIfGoingOnBatteries>false</StopIfGoingOnBatteries><ExecutionTimeLimit>PT0S</ExecutionTimeLimit></Settings><Actions Context="Author"><Exec><Command>{exe}</Command></Exec></Actions></Task>'''
                p=self.store.root/'startup.xml';p.write_text(xml,encoding='utf-16');args=['schtasks','/Create','/TN',name,'/XML',str(p),'/F']
            else:args=['schtasks','/Delete','/TN',name,'/F']
            result=subprocess.run(args,capture_output=True,text=True,creationflags=0x08000000)
            if result.returncode:raise RuntimeError(result.stdout+result.stderr)
            self.cfg['startup']=v;self.persist()
        except Exception as e:self.fail(e)
        self.changed.emit()
    @Slot(bool,bool)
    def monitoringOptions(self,enabled,background):
        previous=(self.cfg['monitorEnabled'],self.cfg['monitorBackground'])
        try:
            self.cfg.update(monitorEnabled=enabled,monitorBackground=background)
            try:self.persist()
            except Exception:
                self.cfg.update(monitorEnabled=previous[0],monitorBackground=previous[1]);raise
            self.monitor.configure(enabled,background,self.accepted)
        except Exception as e:self.fail(e)
        self.changed.emit()
    @Slot()
    def openLogs(self):os.startfile(self.logs.root)
    @Slot()
    def requestClose(self):
        if not self.accepted:
            self.requestExit();return
        if self.trayAvailable:self.hideRequested.emit()
        else:
            self.error='系统托盘当前不可用，已保留窗口。请使用“恢复并退出”结束程序。';self.changed.emit()
    @Slot()
    def requestShow(self):self.showRequested.emit()
    @Slot()
    def requestExit(self):
        if self.shutdown():self.exitRequested.emit()
        else:self.showRequested.emit()
    @Slot(result=bool)
    def shutdown(self):
        try:
            if self.session:self.session.disable()
            if self.hw:self.hw.close();self.hw=None
            self.active=False;self.operational=False;self.timer.stop();self.house.stop()
            self.monitor.close();logging.info('exit_restored');return True
        except Exception as e:self.fail(e);return False

def main():
    QQuickStyle.setStyle('Basic')
    app=QApplication(sys.argv);app.setApplicationName('LecooDesk');app.setWindowIcon(QIcon(str(ROOT/'icon.ico')));app.setOrganizationName('LecooDesk');app.setQuitOnLastWindowClosed(False);style(app)
    socket=QLocalSocket();name='LecooDesk-demo-v1' if MOCK else 'LecooDesk-hardware-v1';socket.connectToServer(name)
    if socket.waitForConnected(250):socket.write(b'show');socket.flush();socket.waitForBytesWritten(200);return 0
    QLocalServer.removeServer(name);server=QLocalServer()
    if not server.listen(name):raise RuntimeError('无法取得单实例锁')
    c=Controller()
    qInstallMessageHandler(lambda kind,context,text:logging.getLogger('qt').log(logging.ERROR if kind in (QtMsgType.QtCriticalMsg,QtMsgType.QtFatalMsg) else logging.WARNING if kind==QtMsgType.QtWarningMsg else logging.DEBUG,'%s:%s %s',context.file,context.line,text))
    engine=QQmlApplicationEngine();engine.rootContext().setContextProperty('backend',c);engine.rootContext().setContextProperty('powerMonitor',c.monitor);engine.load(QUrl.fromLocalFile(str(ROOT/'Main.qml')))
    if not engine.rootObjects():c.shutdown();return 1
    tray=TrayManager(app,engine.rootObjects()[0],c,ROOT/'icon.ico')
    def show_existing():
        peer=server.nextPendingConnection()
        if peer:peer.close();peer.deleteLater()
        tray.show_window()
    server.newConnection.connect(show_existing)
    QTimer.singleShot(0,c.begin)
    if '--smoke' in sys.argv:
        def accept_mock():
            engine.rootObjects()[0].grabWindow().save(str(c.store.root/'packaged-warning.png'))
            c.acceptRisk(False)
        QTimer.singleShot(350,accept_mock)
        QTimer.singleShot(1400,lambda:(engine.rootObjects()[0].grabWindow().save(str(c.store.root/'packaged-preview.png')),c.requestExit()))
    app.aboutToQuit.connect(c.shutdown)
    try:return app.exec()
    finally:c.shutdown()
if __name__=='__main__':sys.exit(main())
