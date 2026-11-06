"""Bounded local history, independent of diagnostic logging."""
import sqlite3,time,uuid,math
from pathlib import Path
class History:
 def __init__(self,path):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
  self.db=sqlite3.connect(self.path,timeout=.3)
  self.db.execute('PRAGMA page_size=4096');self.db.execute('PRAGMA temp_store=MEMORY');self.db.execute('PRAGMA journal_mode=DELETE');self.db.execute('PRAGMA max_page_count=2048')
  self.db.execute('PRAGMA journal_size_limit=0');self.db.execute('PRAGMA secure_delete=ON')
  self.db.execute('CREATE TABLE IF NOT EXISTS points (t REAL, segment TEXT, bucket INTEGER, n INTEGER, sn INTEGER, ss REAL, sl REAL, sh REAL, pn INTEGER, ps REAL, pl REAL, ph REAL, ac INTEGER, quality TEXT, PRIMARY KEY(segment,bucket))')
  self.db.execute('CREATE INDEX IF NOT EXISTS points_time ON points(t)')
  self.db.execute('CREATE TABLE IF NOT EXISTS events(t REAL, kind TEXT)')
  self.db.commit();self.maintain(time.time())
 def add(self,t,segment,sample):
  soc=sample.get('soc');power=sample.get('power')
  for v in (soc,power):
   if v is not None and not math.isfinite(v):raise ValueError('non-finite telemetry')
  with self.db:
   self.db.execute('INSERT INTO points VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(t,segment,-round(t*1000),1,int(soc is not None),soc or 0,soc,soc,int(power is not None),power or 0,power,power,int(sample['ac']),sample.get('quality','')))
 def event(self,t,kind):
  with self.db:self.db.execute('INSERT INTO events VALUES (?,?)',(t,kind))
 def maintain(self,now):
  cutoff=now-600;expiry=now-86400
  # Aggregate complete 30-second buckets only, avoiding a mixed raw/bucket boundary.
  cutoff=min(cutoff,int(cutoff//30)*30)
  with self.db:
   self.db.execute('DELETE FROM points WHERE t<? OR t>?',(expiry,now+60))
   self.db.execute('DELETE FROM events WHERE t<? OR t>?',(expiry,now+60))
   groups=self.db.execute('SELECT segment,CAST(t/30 AS INTEGER),MIN(t),SUM(n),SUM(sn),SUM(ss),MIN(sl),MAX(sh),SUM(pn),SUM(ps),MIN(pl),MAX(ph),MIN(ac),MAX(ac),GROUP_CONCAT(DISTINCT quality) FROM points WHERE bucket<0 AND t<? GROUP BY segment,CAST(t/30 AS INTEGER)',(cutoff,)).fetchall()
   for seg,bucket,t,n,sn,ss,sl,sh,pn,ps,pl,ph,ac,acmax,quality in groups:
    # Mark changes within a bucket as mixed; never invent a clean AC state.
    quality=(quality or '').strip(',')
    if ac!=acmax:quality+='；电源状态变化'
    self.db.execute('INSERT INTO points VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(segment,bucket) DO UPDATE SET n=n+excluded.n,sn=sn+excluded.sn,ss=ss+excluded.ss,sl=MIN(COALESCE(sl,excluded.sl),COALESCE(excluded.sl,sl)),sh=MAX(COALESCE(sh,excluded.sh),COALESCE(excluded.sh,sh)),pn=pn+excluded.pn,ps=ps+excluded.ps,pl=MIN(COALESCE(pl,excluded.pl),COALESCE(excluded.pl,pl)),ph=MAX(COALESCE(ph,excluded.ph),COALESCE(excluded.ph,ph)),quality=CASE WHEN quality=excluded.quality THEN quality ELSE quality||\';\'||excluded.quality END',(t,seg,bucket,n,sn,ss,sl,sh,pn,ps,pl,ph,ac,quality))
   self.db.execute('DELETE FROM points WHERE bucket<0 AND t<?',(cutoff,))
   # Bound event storms and timestamps even if the host clock or source behaves badly.
   self.db.execute('DELETE FROM events WHERE rowid NOT IN (SELECT rowid FROM events ORDER BY t DESC LIMIT 4096)')
  if self.size()>18*1024*1024:raise RuntimeError('历史数据接近20MB预算，采集已暂停')
 def rows(self,now):
  result=[];previous=None
  for t,seg,bucket,n,sn,ss,sl,sh,pn,ps,pl,ph,ac,quality in self.db.execute('SELECT * FROM points WHERE t>=? AND t<=? ORDER BY t',(now-86400,now+1)):
   gap=previous is None or previous[1]!=seg or t-previous[0]>75
   result.append(dict(t=t*1000,soc=ss/sn if sn else None,socMin=sl,socMax=sh,power=ps/pn if pn else None,powerMin=pl,powerMax=ph,ac=bool(ac),quality=quality,gap=gap,aggregate=bucket>=0))
   previous=(t,seg)
  return result
 def events(self,now):return [dict(t=t*1000,kind=k) for t,k in self.db.execute('SELECT t,kind FROM events WHERE t>=? ORDER BY t',(now-86400,))]
 def size(self):return sum(f.stat().st_size for f in self.path.parent.glob(self.path.name+'*') if f.is_file())
 def close(self):self.db.close()
