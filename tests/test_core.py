import sys,pathlib,tempfile,unittest,json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from core import ChargeSession,Store,Logs
from hardware import MockHardware
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.store=Store(pathlib.Path(self.tmp.name));self.hw=MockHardware();self.s=ChargeSession(self.hw,self.store)
 def tearDown(self):self.tmp.cleanup()
 def test_restore_original(self):
  self.hw.values=[90,70];self.s.enable(65,80);self.assertEqual(self.hw.pair(),[80,65]);self.s.disable();self.assertEqual(self.hw.pair(),[90,70]);self.assertFalse((self.store.root/'recovery.json').exists())
 def test_gap(self):
  for pair in [(71,80),(80,70),(-1,80),(0,101)]:
   with self.assertRaises(ValueError):self.s.enable(*pair)
  self.s.enable(0,10);self.assertEqual(self.hw.pair(),[10,0])
 def test_crash_recovery(self):
  self.s.enable(65,80);new=ChargeSession(self.hw,self.store);new.recover();self.assertEqual(self.hw.pair(),[0,0])
 def test_external_change(self):
  self.s.enable(65,80);self.hw.values=[83,70]
  with self.assertRaises(RuntimeError):self.s.enable(60,80)
  self.assertEqual(self.hw.pair(),[83,70])
 def test_partial_write(self):
  original=self.hw.set_pair
  def fail_once(p):
   self.hw.set_pair=original;self.hw.values=[0,p[1]];raise RuntimeError('injected')
  self.hw.set_pair=fail_once
  with self.assertRaises(RuntimeError):self.s.enable(65,80)
  self.assertEqual(self.hw.pair(),[0,0])
 def test_corrupt_recovery(self):
  self.store.save('recovery.json',{'original':[999,0]})
  with self.assertRaises(RuntimeError):self.s.recover()
 def test_retention(self):
  import os,time,logging
  root=self.store.root/'logs';logs=Logs(root);old=root/'old.log';old.write_text('old');os.utime(old,(time.time()-8000,)*2);logs.configure(1,1);self.assertFalse(old.exists());logs.configure(0,1)
if __name__=='__main__':unittest.main()

