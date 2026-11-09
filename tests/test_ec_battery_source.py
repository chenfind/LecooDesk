import sys,pathlib,unittest,threading
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'src'))
from hardware import Hardware
from ec_battery_source import ExperimentalBatterySource
class Tests(unittest.TestCase):
 def test_signed_cache_and_double_read(self):
  hw=object.__new__(Hardware);calls=[];values={0x8f3:0x48,0x8f4:0xf4,0x491:0x80,0x492:0x3e}
  hw.read=lambda a:(calls.append(a) or values[a])
  data=hw.battery_telemetry();self.assertLess(data['ec_power_w'],0);self.assertEqual(data['ec_raw_current'],-3000);self.assertEqual(data['ec_voltage_mv'],16000);self.assertEqual(len(calls),8)
 def test_unstable_word_is_unknown(self):
  hw=object.__new__(Hardware);n=[0]
  def read(a):n[0]+=1;return n[0]%251
  hw.read=read
  with self.assertRaises(RuntimeError):hw.battery_telemetry()
 def test_worker_never_touches_hardware_and_preserves_windows(self):
  controller=threading.get_ident()
  class HW:
   def battery_telemetry(self):
    assert threading.get_ident()==controller
    return {'ec_power_w':-12.5}
  class Native:
   def sample(self):return dict(soc=70,power=34.,quality='critical',ac=True)
  source=ExperimentalBatterySource(lambda:HW(),Native());source.prepare();result=[]
  t=threading.Thread(target=lambda:result.append(source.sample()));t.start();t.join()
  self.assertEqual(result[0]['power'],-12.5);self.assertEqual(result[0]['windows_power_w'],34);self.assertIn('critical',result[0]['quality'])
 def test_failure_does_not_fall_back_to_misleading_windows_watts(self):
  class Native:
   def sample(self):return dict(power=34.,quality='',ac=True)
  source=ExperimentalBatterySource(lambda:None,Native());source.prepare();r=source.sample()
  self.assertIsNone(r['power']);self.assertEqual(r['windows_power_w'],34);self.assertIn('未知',r['quality'])
if __name__=='__main__':unittest.main()
