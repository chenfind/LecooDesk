from pathlib import Path
import struct,os
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtGui import QGuiApplication,QImage,QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QByteArray,QBuffer,QIODevice,Qt
root=Path(__file__).resolve().parent
app=QGuiApplication([]);im=QImage(256,256,QImage.Format_ARGB32);im.fill(Qt.transparent);p=QPainter(im);QSvgRenderer(str(root/'src'/'icon.svg')).render(p);p.end();data=QByteArray();buf=QBuffer(data);buf.open(QIODevice.WriteOnly);assert im.save(buf,'PNG');raw=bytes(data);(root/'src'/'icon.ico').write_bytes(struct.pack('<HHH',0,1,1)+struct.pack('<BBBBHHII',0,0,0,0,1,32,len(raw),22)+raw)
