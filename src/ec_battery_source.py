"""Experimental EC meter snapshot prepared exclusively on the controller thread.
The worker uses only copied values plus Windows QUERY_STATUS; no worker EC IO.
"""
from battery_source import NativeBatterySource
class ExperimentalBatterySource:
 def __init__(self,get_hardware,native=None):
  self.get_hardware=get_hardware;self.native=native or NativeBatterySource();self.prepared={};self.prepare_error='尚未取得电量计数据'
 def prepare(self):
  self.prepared={}
  try:
   hw=self.get_hardware()
   if hw is None:raise RuntimeError('硬件未就绪')
   self.prepared=dict(hw.battery_telemetry());self.prepare_error=''
  except Exception as e:self.prepare_error=str(e)
 def sample(self):
  result=dict(self.native.sample());result['windows_power_w']=result.get('power');result['windows_quality']=result.get('quality','')
  result['power']=self.prepared.get('ec_power_w');result.update(self.prepared)
  result['experimental_ec']=True;result['source']='EC meter cache (experimental, firmware scale, uncalibrated)'
  result['quality']='实验性电量计功率，未外部校准'
  result['ec_measurement_error']=self.prepare_error
  if self.prepare_error:result['quality']+='；功率未知：'+self.prepare_error
  if result['windows_quality']:result['quality']+='；Windows数据提示：'+result['windows_quality']
  return result
