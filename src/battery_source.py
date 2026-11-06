"""Read-only Windows battery-class queries. No EC/SMBus or SET IOCTLs."""
import ctypes as c
from ctypes import wintypes as w
import uuid,time,json,pathlib,datetime,argparse
class GUID(c.Structure):_fields_=[('data',c.c_ubyte*16)]
class Interface(c.Structure):_fields_=[('size',w.DWORD),('guid',GUID),('flags',w.DWORD),('reserved',c.c_void_p)]
class Wait(c.Structure):_fields_=[('tag',w.ULONG),('timeout',w.ULONG),('state',w.ULONG),('low',w.ULONG),('high',w.ULONG)]
class Status(c.Structure):_fields_=[('state',w.ULONG),('capacity',w.ULONG),('voltage',w.ULONG),('rate',w.LONG)]
class Query(c.Structure):_fields_=[('tag',w.ULONG),('level',c.c_int),('at_rate',w.LONG)]
class Info(c.Structure):_fields_=[('capabilities',w.ULONG),('technology',c.c_ubyte),('reserved',c.c_ubyte*3),('chemistry',c.c_char*4),('design',w.ULONG),('full',w.ULONG),('alert1',w.ULONG),('alert2',w.ULONG),('bias',w.ULONG),('cycles',w.ULONG)]
s=c.WinDLL('setupapi',use_last_error=True);k=c.WinDLL('kernel32',use_last_error=True)
s.SetupDiGetClassDevsW.argtypes=[c.POINTER(GUID),w.LPCWSTR,w.HWND,w.DWORD];s.SetupDiGetClassDevsW.restype=c.c_void_p
s.SetupDiEnumDeviceInterfaces.argtypes=[c.c_void_p,c.c_void_p,c.POINTER(GUID),w.DWORD,c.POINTER(Interface)]
s.SetupDiGetDeviceInterfaceDetailW.argtypes=[c.c_void_p,c.POINTER(Interface),c.c_void_p,w.DWORD,c.POINTER(w.DWORD),c.c_void_p]
s.SetupDiDestroyDeviceInfoList.argtypes=[c.c_void_p]
k.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,c.c_void_p,w.DWORD,w.DWORD,w.HANDLE];k.CreateFileW.restype=w.HANDLE
k.DeviceIoControl.argtypes=[w.HANDLE,w.DWORD,c.c_void_p,w.DWORD,c.c_void_p,w.DWORD,c.POINTER(w.DWORD),c.c_void_p]
k.CloseHandle.argtypes=[w.HANDLE]
def query(h,code,inp,out):
 assert code in (0x294040,0x294044,0x29404c)
 n=w.DWORD()
 if not k.DeviceIoControl(h,code,c.byref(inp),c.sizeof(inp),c.byref(out),c.sizeof(out),c.byref(n),None):raise c.WinError(c.get_last_error())
 if n.value<c.sizeof(out):raise RuntimeError('Short battery response')
 return out
def paths():
 g=GUID();g.data[:]=uuid.UUID('72631e54-78a4-11d0-bcf7-00aa00b7b32a').bytes_le
 d=s.SetupDiGetClassDevsW(c.byref(g),None,None,0x12)
 if d==c.c_void_p(-1).value:raise c.WinError(c.get_last_error())
 try:
  i=0
  while True:
   it=Interface();it.size=c.sizeof(it)
   if not s.SetupDiEnumDeviceInterfaces(d,None,c.byref(g),i,c.byref(it)):
    if c.get_last_error()==259:break
    raise c.WinError(c.get_last_error())
   n=w.DWORD();s.SetupDiGetDeviceInterfaceDetailW(d,c.byref(it),None,0,c.byref(n),None)
   if not 8<=n.value<=65536:raise RuntimeError('电池接口返回的路径长度无效')
   buf=c.create_string_buffer(n.value);c.cast(buf,c.POINTER(w.DWORD))[0]=8 if c.sizeof(c.c_void_p)==8 else 6
   if not s.SetupDiGetDeviceInterfaceDetailW(d,c.byref(it),buf,n,None,None):raise c.WinError(c.get_last_error())
   yield c.wstring_at(c.addressof(buf)+4)
   i+=1
 finally:s.SetupDiDestroyDeviceInfoList(d)

# Reserved capabilities remain hidden until independently validated sources exist.
CAPABILITIES={'battery_percent':True,'battery_power_w':True,'adapter_output_w':False,'system_draw_w':False}

def normalize(status,info):
 relative=bool(info.capabilities&0x40000000)
 soc=None if status.capacity==0xffffffff or info.full in (0,0xffffffff) else round(100*status.capacity/info.full,1)
 if soc is not None and not 0<=soc<=100:soc=None
 power=None if relative or status.rate==-2147483648 else status.rate/1000
 ac=bool(status.state&1);quality=[]
 if power is None:quality.append('功率不可用')
 if soc is None:quality.append('电量不可用')
 if not ac and (status.state&4 or power is not None and power>0):quality.append('离线却上报充电')
 if status.state&6==6:quality.append('充放电标志冲突')
 if status.state&8 and soc is not None and soc>10:quality.append('状态标志与电量不协调')
 return {'soc':soc,'power':power,'ac':ac,'quality':'；'.join(quality),'state':status.state,'source':'Windows battery QUERY_STATUS'}

class NativeBatterySource:
 def sample(self):
  devices=list(paths())
  if len(devices)!=1:raise RuntimeError('当前监测仅支持单块系统电池')
  h=k.CreateFileW(devices[0],0x80000000,3,None,3,0,None)
  if h==w.HANDLE(-1).value:raise c.WinError(c.get_last_error())
  try:
   tag=query(h,0x294040,w.ULONG(0),w.ULONG()).value
   if not tag:raise RuntimeError('电池标识暂不可用')
   info=query(h,0x294044,Query(tag,0,0),Info())
   status=query(h,0x29404c,Wait(tag,0,0,0,0),Status())
   return normalize(status,info)
  finally:k.CloseHandle(h)

class DemoBatterySource:
 def sample(self):
  import math
  t=time.time()
  return {'soc':round(65+10*math.sin(t/900),1),'power':round(12*math.sin(t/70),2),'ac':True,'quality':'模拟数据','state':1,'source':'demo'}
