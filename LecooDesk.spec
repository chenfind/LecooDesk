# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
root=Path(SPECPATH)
a=Analysis([str(root/'src'/'main.py')],pathex=[str(root/'src')],binaries=[],datas=[(str(root/'src'/'Main.qml'),'.'),(str(root/'src'/'icon.ico'),'.')],hiddenimports=[],hookspath=[str(root/'hooks')],hooksconfig={},runtime_hooks=[],excludes=['PySide6.QtWebEngineCore','PySide6.QtWebEngineWidgets','PySide6.QtPdf'],noarchive=False)
# Qt 6.12 Windows uses the OS ICU API. Do not bundle similarly named,
# incompatible ICU libraries discovered on the build host PATH.
a.binaries=[item for item in a.binaries if Path(item[0]).name.lower() not in ('icuuc.dll','icudt78.dll')]
pyz=PYZ(a.pure)
options=dict(exclude_binaries=True,debug=False,bootloader_ignore_signals=False,strip=False,upx=True,console=False,disable_windowed_traceback=False,icon=str(root/'src'/'icon.ico'))
exe=EXE(pyz,a.scripts,[],name='LecooDesk',uac_admin=True,**options)
demo=EXE(pyz,a.scripts,[],name='LecooDesk-demo',uac_admin=False,**options)
diag_options=dict(options,console=True)
diag=EXE(pyz,a.scripts,[],name='LecooDesk-diagnostics',uac_admin=False,**diag_options)
coll=COLLECT(exe,demo,diag,a.binaries,a.datas,strip=False,upx=True,name='LecooDesk')



