"""Create distributable/source archives from a committed working tree after build.ps1."""
from pathlib import Path
import zipfile,subprocess,hashlib
ROOT=Path(__file__).resolve().parent

def package():
 folder=ROOT/'dist'/'LecooDesk'
 if not (folder/'LecooDesk.exe').is_file():raise RuntimeError('Run build.ps1 first')
 status=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)
 if status.strip():raise RuntimeError('Commit source changes before packaging')
 for name in ('logs','logs-demo'):
  if (folder/name).exists():raise RuntimeError('Archive runtime logs outside dist/LecooDesk before packaging')
 target=ROOT/'dist'/'LecooDesk-Windows.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for f in folder.rglob('*'):
   if f.is_file():z.write(f,Path('dist/LecooDesk')/f.relative_to(folder))
  for name in ('README.md','install.ps1','THIRD_PARTY_NOTICES.md','CHANGELOG.md'):
   z.write(ROOT/name,name)
  for name in ('docs','LICENSES'):
   for f in (ROOT/name).rglob('*'):
    if f.is_file():z.write(f,f.relative_to(ROOT))
 source=ROOT/'dist'/'LecooDesk-Source.zip'
 subprocess.run(['git','archive','--format=zip','--output='+str(source),'HEAD'],cwd=ROOT,check=True)
 lines=[hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.name for f in (target,source)]
 (ROOT/'dist'/'SHA256SUMS.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 print('\n'.join(lines))
if __name__=='__main__':package()
