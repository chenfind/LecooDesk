import json,os,time,logging,logging.handlers,pathlib
from settings import valid_range
class Logs:
 def __init__(self,root):self.root=root;root.mkdir(parents=True,exist_ok=True);self.handler=None
 def configure(self,level,hours):
  logger=logging.getLogger();logger.setLevel(logging.DEBUG if level==2 else logging.INFO)
  if self.handler:logger.removeHandler(self.handler);self.handler.close()
  self.handler=logging.handlers.RotatingFileHandler(self.root/(time.strftime('%Y%m%d-%H')+'.log'),maxBytes=2*1024*1024,backupCount=20,encoding='utf-8') if level else logging.NullHandler()
  self.handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s'));logger.addHandler(self.handler)
  self.cleanup(hours)
 def cleanup(self,hours):
  current=pathlib.Path(self.handler.baseFilename) if hasattr(self.handler,'baseFilename') else None
  for p in self.root.glob('*.log*'):
   if p!=current and p.is_file() and time.time()-p.stat().st_mtime>hours*3600:
    try:p.unlink()
    except OSError:pass
class Store:
 def __init__(self,root):self.root=root;root.mkdir(parents=True,exist_ok=True)
 def load(self,name,default):
  p=self.root/name
  if not p.exists():return default
  return json.loads(p.read_text(encoding='utf-8'))
 def save(self,name,data):
  p=self.root/name;tmp=p.with_suffix('.tmp')
  with tmp.open('w',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
  os.replace(tmp,p)
 def remove(self,name):(self.root/name).unlink(missing_ok=True)
class ChargeSession:
 def __init__(self,hw,store):self.hw=hw;self.store=store;self.original=None;self.expected=None
 def recover(self):
  old=self.store.load('recovery.json',None)
  if old is None:return
  p=old['original']
  if not isinstance(p,list) or len(p)!=2 or any(type(v)!=int or not 0<=v<=100 for v in p):raise RuntimeError('恢复记录无效')
  self.hw.set_pair(p);self.store.remove('recovery.json');logging.info('recovered previous session original=%s',p)
 def enable(self,low,high):
  if not valid_range(low,high):raise ValueError('上下限间隔必须至少为 10%')
  if self.expected is not None and self.hw.pair()!=self.expected:raise RuntimeError('阈值被其他程序改变，请先停止限制')
  if self.original is None:
   self.original=self.hw.pair()
   if any(type(v)!=int or not 0<=v<=100 for v in self.original) or (self.original != [0,0] and self.original[0]<=self.original[1]):
    self.original=None;raise RuntimeError('当前阈值无效，拒绝修改')
   self.store.save('recovery.json',{'original':self.original,'time':time.time()})
  try:self.hw.set_pair([high,low]);self.expected=[high,low];logging.info('charge_enabled lower=%d upper=%d original=%s',low,high,self.original)
  except:
   self.disable();raise
 def disable(self):
  if self.original is not None:
   self.hw.set_pair(self.original);self.store.remove('recovery.json');logging.info('charge_restored original=%s',self.original);self.original=None;self.expected=None


