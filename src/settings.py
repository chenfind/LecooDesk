from pathlib import Path
import json,uuid,os
DEFAULTS={'enabled':False,'low':65,'high':80,'logLevel':2,'hours':72,'startup':False,'theme':'system','warningDismissed':False,'monitorEnabled':True,'monitorBackground':True,'monitorSource':'windows'}
WARNING_TEXT=('LecooDesk 是个人实验性硬件控制软件，未经厂商认证，也未经过广泛机型验证。'
'作者不能保证功能有效、运行稳定或操作安全。使用本软件可能导致充电异常、系统崩溃、数据丢失，甚至机器或电池损坏；重启不一定能够恢复。'
'作者不承担因使用本软件产生的损失或责任。请先保存工作并备份重要数据，充分理解风险后谨慎决定是否继续。若不能接受，请立即退出。')
def valid_range(low,high):
 return type(low)==int and type(high)==int and 0<=low<high<=100 and high-low>=10

def validate_settings(c):
 if not valid_range(c['low'],c['high']):raise ValueError('两个阈值必须相差至少 10 个百分点')
 if any(type(c[k])!=bool for k in ('enabled','startup','warningDismissed','monitorEnabled','monitorBackground')):raise ValueError('开关设置无效')
 if type(c['logLevel'])!=int or c['logLevel'] not in (0,1,2):raise ValueError('日志级别无效')
 if type(c['hours'])!=int or not 1<=c['hours']<=720:raise ValueError('日志保留时长无效')
 if c['monitorSource'] not in ('windows','ec'):raise ValueError('功率来源无效')
 if c['theme'] not in ('system','dark','light'):raise ValueError('主题设置无效')

def choose_log_directory(install_dir,fallback,mock=False):
 preferred=Path(install_dir)/('logs-demo' if mock else 'logs')
 try:
  preferred.mkdir(parents=True,exist_ok=True)
  probe=preferred/('.write-check-'+uuid.uuid4().hex)
  with probe.open('xb') as f:f.write(b'')
  probe.unlink()
  return preferred,''
 except OSError as e:
  fallback=Path(fallback)/'logs';fallback.mkdir(parents=True,exist_ok=True)
  return fallback,'安装目录不可写，日志已回退到：'+str(fallback)+'（'+str(e)+'）'
