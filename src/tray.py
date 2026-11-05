from PySide6.QtWidgets import QSystemTrayIcon,QMenu
from PySide6.QtGui import QIcon

class TrayManager:
    def __init__(self,app,window,controller,icon_path):
        self.app=app;self.window=window;self.controller=controller
        self.icon=None;self.menu=None;self.notified=False
        controller.showRequested.connect(self.show_window)
        controller.hideRequested.connect(self.hide_window)
        controller.exitRequested.connect(self.quit)
        if not QSystemTrayIcon.isSystemTrayAvailable():
            controller.trayAvailable=False
            return
        self.icon=QSystemTrayIcon(QIcon(str(icon_path)),app)
        self.menu=QMenu()
        self.menu.addAction('显示主界面',self.show_window)
        self.menu.addSeparator()
        self.menu.addAction('恢复原设置并退出',controller.requestExit)
        self.icon.setContextMenu(self.menu)
        self.icon.activated.connect(self.activated)
        controller.changed.connect(self.refresh)
        self.icon.show();controller.trayAvailable=True;self.refresh()
    def show_window(self):
        self.window.showNormal();self.window.raise_();self.window.requestActivate()
    def hide_window(self):
        if self.icon is None:return
        self.window.hide()
        if not self.notified:
            self.icon.showMessage('LecooDesk 仍在运行','窗口已收起到系统托盘。需要退出时，请右键托盘图标并选择“恢复原设置并退出”。')
            self.notified=True
    def activated(self,reason):
        if reason in (QSystemTrayIcon.Trigger,QSystemTrayIcon.DoubleClick):self.show_window()
    def refresh(self):
        if self.icon:
            text='限制生效' if self.controller.active else '限制未生效'
            self.icon.setToolTip('LecooDesk · '+text)
    def quit(self):
        if self.icon:self.icon.hide()
        self.app.quit()
