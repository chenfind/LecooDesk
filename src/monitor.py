"""Asynchronous read-only sampler; lifecycle is separate from EC charge control."""
import time,uuid,logging
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtCore import QObject,Signal,Property,Slot,QTimer
from history import History
from battery_source import NativeBatterySource,DemoBatterySource
class Monitor(QObject):
 changed=Signal()
 def __init__(self,path,mock=False,source=None):
  super().__init__();self.path=path;self.mock=mock;self.source=source or (DemoBatterySource() if mock else NativeBatterySource())
  self.history=None;self.pool=None;self.future=None;self.generation=0;self.allowed=False;self.enabled=True;self.background=True;self.visible=True;self.closed=False
  self.segment=uuid.uuid4().hex;self.last_time=None;self.last_ac=None;self.last={};self.error='';self.points=[];self.event_rows=[];self.now=time.time();self.next_due=0;self.last_maintenance=0
  self.timer=QTimer(self);self.timer.setInterval(200);self.timer.timeout.connect(self.tick);self.timer.start()
 def active(self):return self.allowed and self.enabled and (self.visible or self.background) and not self.closed and not self.error
 def interval(self):return 2 if self.visible else 30
 @Property('QVariantMap',notify=changed)
 def state(self):
  return dict(enabled=self.enabled,background=self.background,collecting=self.active(),interval=self.interval(),points=self.points,events=self.event_rows,latest=self.last,error=self.error,now=self.now*1000,path=str(self.path),bytes=self.history.size() if self.history else 0,mock=self.mock)
 def configure(self,enabled,background,allowed):
  if allowed and self.history is None and not self.closed:
   try:
    self.history=History(self.path);self.now=time.time();self.points=self.history.rows(self.now);self.event_rows=self.history.events(self.now)
   except Exception as e:self.error='历史记录不可用：'+str(e)
  old=self.active();self.enabled=enabled;self.background=background;self.allowed=allowed
  if not self.active() or not old:self.generation+=1;self.segment=uuid.uuid4().hex;self.last_time=None
  if self.active() and not old:self.next_due=0
  if self.history and old!=self.active():self.note('恢复采集' if self.active() else '暂停采集')
  self.changed.emit()
 @Slot(bool)
 def setVisible(self,visible):
  if self.visible==visible:return
  was=self.active();self.visible=visible
  if was and not self.active():self.generation+=1;self.segment=uuid.uuid4().hex;self.last_time=None
  if self.active():self.next_due=time.monotonic()+self.interval()
  if self.history and was!=self.active():self.note('恢复采集' if self.active() else '暂停采集')
  self.changed.emit()
 def note(self,kind):
  try:self.history.event(time.time(),kind)
  except Exception as e:self.error='历史事件写入失败，采集暂停：'+str(e);logging.exception('monitor_event_failed')
 def tick(self):
  if self.closed:return
  now=time.time()
  if self.history and now-self.last_maintenance>=60:
   try:
    self.history.maintain(now);self.last_maintenance=now;self.now=now;self.points=self.history.rows(now);self.event_rows=self.history.events(now);self.changed.emit()
   except Exception as e:self.error='历史维护失败，采集暂停：'+str(e);self.last_maintenance=now;self.changed.emit()
  if self.future and self.future[0].done():
   future,generation=self.future;self.future=None
   try:
    sample=future.result()
    if generation==self.generation and self.active():self.record(sample)
   except Exception as e:
    if generation==self.generation and self.active():self.error='采集暂停：'+str(e);logging.exception('monitor_failed');self.changed.emit()
  if self.active() and self.future is None and time.monotonic()>=self.next_due:
   if self.pool is None:self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='battery-query')
   self.future=(self.pool.submit(self.source.sample),self.generation);self.next_due=time.monotonic()+self.interval()
 def record(self,sample):
  now=time.time()
  if self.history is None:self.history=History(self.path)
  if self.last_time is not None and (now-self.last_time>max(8,self.interval()*2.5) or now<=self.last_time):
   self.segment=uuid.uuid4().hex;self.history.event(now,'采样中断 / 系统恢复')
  if self.last_ac is not None and self.last_ac!=sample['ac']:self.history.event(now,'接入外接电源' if sample['ac'] else '断开外接电源')
  logging.debug('monitor_sample %s',sample)
  self.history.add(now,self.segment,sample)
  if now-self.last_maintenance>=60:self.history.maintain(now);self.last_maintenance=now
  self.last_time=now;self.last_ac=sample['ac'];self.last=dict(sample,t=now*1000);self.now=now
  self.points=self.history.rows(now);self.event_rows=self.history.events(now);self.changed.emit()
 @Slot()
 def retry(self):
  self.error='';self.segment=uuid.uuid4().hex;self.last_time=None;self.next_due=0;self.generation+=1;self.changed.emit()
 def close(self):
  if self.closed:return
  self.closed=True;self.generation+=1;self.timer.stop()
  if self.pool:self.pool.shutdown(wait=False,cancel_futures=True)
  if self.history:self.history.close();self.history=None
