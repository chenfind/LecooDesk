import sys,pathlib,tempfile,unittest,time,os,threading
from unittest.mock import patch
os.environ['QT_QPA_PLATFORM']='offscreen'
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from history import History
from monitor import Monitor
from battery_source import normalize,Status,Info,CAPABILITIES
app=QApplication.instance() or QApplication([])
SAMPLE=dict(soc=65.,power=0.,ac=True,quality='',state=1)
class HistoryTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.h=History(pathlib.Path(self.tmp.name)/'power.sqlite3');self.now=time.time()
 def tearDown(self):self.h.close();self.tmp.cleanup()
 def test_aggregation_preserves_sign_peaks_and_unknown(self):
  t=int((self.now-1000)//30)*30+1
  for dt,power in ((0,-20),(2,10),(4,None)):self.h.add(t+dt,'a',dict(SAMPLE,power=power))
  self.h.maintain(self.now);rows=self.h.rows(self.now)
  self.assertEqual(len(rows),1);self.assertEqual(rows[0]['power'],-5);self.assertEqual(rows[0]['powerMin'],-20);self.assertEqual(rows[0]['powerMax'],10);self.assertTrue(rows[0]['aggregate'])
 def test_retention_restart_gaps_and_recent_raw(self):
  self.h.add(self.now-90000,'old',SAMPLE);self.h.add(self.now-4,'a',SAMPLE);self.h.add(self.now-2,'b',dict(SAMPLE,power=None))
  self.h.maintain(self.now);rows=self.h.rows(self.now);self.assertEqual(len(rows),2);self.assertTrue(rows[1]['gap']);self.assertIsNone(rows[1]['power'])
  self.h.close();self.h=History(pathlib.Path(self.tmp.name)/'power.sqlite3');self.assertEqual(len(self.h.rows(self.now)),2)
 def test_incremental_aggregation_handles_initial_unknown(self):
  t=int((self.now-1000)//30)*30+1
  self.h.add(t,'a',dict(SAMPLE,power=None));self.h.maintain(self.now)
  self.h.add(t+2,'a',dict(SAMPLE,power=8));self.h.maintain(self.now)
  row=self.h.rows(self.now)[0];self.assertEqual(row['powerMin'],8);self.assertEqual(row['power'],8)
 def test_24h_size_and_counts(self):
  # A full 24-hour foreground workload, inserted in one transaction for test speed.
  values=[]
  for i in range(43200):
   t=self.now-86400+2*i;v=(-1 if i%2 else 1)*20
   values.append((t,'day',-round(t*1000),1,1,65,65,65,1,v,v,v,1,''))
  with self.h.db:self.h.db.executemany('INSERT INTO points VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',values)
  self.h.maintain(self.now);rows=self.h.rows(self.now)
  self.assertLess(len(rows),3200);self.assertLess(self.h.size(),5*1024*1024)
 def test_nonfinite_rejected(self):
  with self.assertRaises(ValueError):self.h.add(self.now,'a',dict(SAMPLE,power=float('nan')))
class SourceTests(unittest.TestCase):
 def test_critical_flag_and_unconfirmed_positive_rate(self):
  i=Info();i.full=80080
  r=normalize(Status(9,64064,16000,34000),i)
  self.assertEqual(r['power'],34)
  self.assertIn('严重状态',r['quality'])
  self.assertIn('实际充放电状态未确认',r['quality'])
  self.assertEqual(normalize(Status(5,64064,16000,34000),i)['quality'],'')

 def test_unknown_relative_and_suspicious_sign_are_not_faked(self):
  i=Info();i.full=80080;s=Status(4,52052,16000,20000);r=normalize(s,i)
  self.assertEqual(r['power'],20);self.assertIn('离线',r['quality'])
  s.rate=-2147483648;self.assertIsNone(normalize(s,i)['power'])
  i.capabilities=0x40000000;s.rate=20000;self.assertIsNone(normalize(s,i)['power'])
  self.assertFalse(CAPABILITIES['adapter_output_w']);self.assertFalse(CAPABILITIES['system_draw_w'])
class MonitorTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.calls=0
  class Source:
   def sample(inner):self.calls+=1;return dict(SAMPLE)
  self.m=Monitor(pathlib.Path(self.tmp.name)/'power.sqlite3',source=Source());self.m.timer.stop()
 def tearDown(self):self.m.close();self.m.deleteLater();app.processEvents();self.tmp.cleanup()
 def settle(self):
  for _ in range(100):
   if self.m.future and self.m.future[0].done():break
   time.sleep(.001)
  self.m.tick()
 def test_consent_disabled_and_background_interval(self):
  self.m.tick();self.assertEqual(self.calls,0)
  self.m.configure(False,True,True);self.m.tick();self.assertEqual(self.calls,0)
  self.m.configure(True,True,True);self.m.tick();self.settle();self.assertEqual(self.calls,1)
  self.m.setVisible(False);self.assertEqual(self.m.interval(),30)
  due=self.m.next_due;self.m.tick();self.assertEqual(self.calls,1);self.assertGreater(due,time.monotonic()+28)
  self.m.configure(True,False,True);self.assertFalse(self.m.active());self.m.tick();self.assertEqual(self.calls,1)
  self.m.setVisible(True);self.assertTrue(self.m.active());self.assertEqual(self.m.interval(),2)
 def test_disable_discards_inflight_result_and_starts_no_new_query(self):
  release=threading.Event();started=threading.Event()
  def sample():self.calls+=1;started.set();release.wait(1);return dict(SAMPLE)
  self.m.source.sample=sample;self.m.configure(True,True,True);self.m.tick();self.assertTrue(started.wait(1))
  self.m.configure(False,True,True);release.set();self.settle();self.assertEqual(self.m.points,[])
  for _ in range(5):self.m.tick()
  self.assertEqual(self.calls,1)
 def test_errors_pause_without_fake_zero_and_can_retry(self):
  self.m.source.sample=lambda:(_ for _ in ()).throw(OSError('unavailable'))
  self.m.configure(True,True,True);self.m.tick();self.settle();self.assertFalse(self.m.active());self.assertEqual(self.m.points,[]);self.assertIn('unavailable',self.m.error)
  self.m.source.sample=lambda:dict(SAMPLE);self.m.retry();self.m.tick();self.settle();self.assertEqual(len(self.m.points),1)
 def test_suspend_gap_and_event(self):
  self.m.configure(True,True,True)
  with patch('monitor.time.time',return_value=time.time()-120):self.m.record(SAMPLE)
  self.m.record(dict(SAMPLE,ac=False,power=-10));self.assertTrue(self.m.points[-1]['gap']);self.assertIn('断开外接电源',[e['kind'] for e in self.m.event_rows])
if __name__=='__main__':unittest.main()
