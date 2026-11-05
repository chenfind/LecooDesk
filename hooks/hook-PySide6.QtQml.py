"""Collect only the Qt QML modules used by this application.
Uses PyInstaller's public Qt hook helpers; no WebEngine, PDF, multimedia or 3D QML.
"""
from pathlib import Path
from PyInstaller.utils.hooks.qt import add_qt6_dependencies,pyside6_library_info
hiddenimports,binaries,datas=add_qt6_dependencies(__file__)
qb,qd=pyside6_library_info.collect_qtqml_files()
def used(item):
 p=Path(item[0]).as_posix()
 if '/qml/' not in p:return False
 r=p.split('/qml/',1)[1].split('/')
 if r[0]=='QtQml':return True
 if r[0]!='QtQuick':return False
 return len(r)==2 or r[1] in ('Controls','Templates','Layouts','Window')
binaries += [x for x in qb if used(x)]
datas += [x for x in qd if used(x)]
