import ctypes as C, ctypes.wintypes as W, struct, logging
log=logging.getLogger('hardware')
class Hardware:
 def __init__(self):
  import winreg
  with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\BIOS') as key:
   model=winreg.QueryValueEx(key,'SystemProductName')[0];bios=winreg.QueryValueEx(key,'BIOSVersion')[0]
  log.info('identity model=%s bios=%s',model,bios)
  if model.strip()!='Lecoo N155A' or bios!='N155A_00_V1.2_PKID':raise RuntimeError('此版本只支持已验证的 N155A / BIOS V1.2，拒绝访问硬件')
  self.k=C.WinDLL('kernel32',use_last_error=True)
  self.k.CreateFileW.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,C.c_void_p,W.DWORD,W.DWORD,C.c_void_p];self.k.CreateFileW.restype=W.HANDLE
  self.k.DeviceIoControl.argtypes=[W.HANDLE,W.DWORD,C.c_void_p,W.DWORD,C.c_void_p,W.DWORD,C.POINTER(W.DWORD),C.c_void_p];self.k.DeviceIoControl.restype=W.BOOL
  self.k.CloseHandle.argtypes=[W.HANDLE]
  self.h=self.k.CreateFileW(r'\\.\inpoutx64',0xC0000000,3,None,3,0,None)
  if self.h==C.c_void_p(-1).value:raise C.WinError(C.get_last_error())
  try:
   chip=[self.read(a) for a in (0x2000,0x2001,0x2002)]
   if chip!=[85,113,7]:raise RuntimeError('芯片校验不符，拒绝硬件操作')
   log.info('chip_verified chip=%s port=0x4e',chip)
  except: self.close();raise
 def ctl(self,code,data,n):
  buf=C.create_string_buffer(data);out=C.create_string_buffer(16);count=W.DWORD()
  if not self.k.DeviceIoControl(self.h,code,buf,len(data),out,n,C.byref(count),None):raise C.WinError(C.get_last_error())
  if code==0x9C402004 and count.value<1:raise RuntimeError('驱动返回空数据')
  return out.raw
 def port(self,p,v):
  if p not in (0x4e,0x4f):raise ValueError('port')
  log.debug('port_select port=%04x value=%02x',p,v)
  self.ctl(0x9C402008,struct.pack('<HB',p,v),16)
 def read(self,a):
  if a not in (0x2000,0x2001,0x2002,0x470,0x493,0x4bb,0x4bc,0x8f3,0x8f4,0x491,0x492):raise ValueError('address')
  log.debug('read_begin addr=%04x',a)
  for p,v in [(0x4e,0x2e),(0x4f,0x11),(0x4e,0x2f),(0x4f,a>>8),(0x4e,0x2e),(0x4f,0x10),(0x4e,0x2f),(0x4f,a&255),(0x4e,0x2e),(0x4f,0x12),(0x4e,0x2f)]:self.port(p,v)
  v=self.ctl(0x9C402004,struct.pack('<H',0x4f),1)[0];log.debug('read addr=%04x value=%d',a,v);return v
 def battery_telemetry(self):
  # Called only on the controller thread, alongside all threshold operations.
  def word(hi,lo):
   for _ in range(3):
    first=(self.read(hi)<<8)|self.read(lo)
    second=(self.read(hi)<<8)|self.read(lo)
    if first==second:return first
   raise RuntimeError('电量计缓存更新中，无法取得一致样本')
  raw=word(0x8f4,0x8f3);voltage=word(0x492,0x491)
  if not 8000<=voltage<=20000:raise RuntimeError('电池电压缓存超出验证范围')
  signed=raw-65536 if raw&0x8000 else raw
  if abs(signed*8/25)>10000:raise RuntimeError('电流缓存超出实验范围')
  return {'ec_raw_current':signed,'ec_voltage_mv':voltage,'ec_current_ma':signed*8/25,'ec_power_w':signed*8/25*voltage/1000000}
 def write(self,a,v):
  if a not in (0x4bb,0x4bc) or not 0<=v<=100:raise ValueError('write')
  self.read(a);self.port(0x4f,v)
  if self.read(a)!=v:raise RuntimeError('写入读回不一致')
  log.info('write_verified addr=%04x value=%d',a,v)
 def snapshot(self):return {'soc':self.read(0x493),'temperature':self.read(0x470)}
 def pair(self):return [self.read(0x4bb),self.read(0x4bc)]
 def set_pair(self,p):
  self.write(0x4bb,0);self.write(0x4bc,p[1]);self.write(0x4bb,p[0])
  if self.pair()!=list(p):raise RuntimeError('阈值校验失败')
 def close(self):
  if self.h:self.k.CloseHandle(self.h);self.h=None
class MockHardware:
 def __init__(self):self.values=[0,0]
 def read(self,a):return {0x493:79,0x470:41}.get(a,0)
 def snapshot(self):return {'soc':79,'temperature':41}
 def pair(self):return self.values.copy()
 def set_pair(self,p):self.values=list(p)
 def close(self):pass


