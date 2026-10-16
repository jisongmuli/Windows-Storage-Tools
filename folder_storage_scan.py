import os,sys,stat,json,gzip,time
from collections import defaultdict
import argparse
parser=argparse.ArgumentParser(description="Read-only directory size scanner; skips reparse points.")
parser.add_argument("--root", default=os.path.expanduser("~"))
parser.add_argument("--output", default="reports/folder-storage-scan.json.gz")
args=parser.parse_args()
BASE=os.path.dirname(os.path.abspath(__file__))
S=defaultdict(int); UNIQUE=defaultdict(int); N=defaultdict(int)
seen_dirs={}; seen_files=set(); aliases={}; errors=[]; root_files=[]
start=time.time(); files=0
root=os.path.abspath(args.root)
stack=[(root,False)]
def priority(parent,name):
    n=name.casefold(); p=parent.casefold()
    if parent==root: return (0 if n=='users' else 1,name)
    if p.endswith('\\appdata'): return ({'roaming':0,'local':1,'locallow':2}.get(n,3),name)
    if p.endswith('\\appdata\\local'): return (9 if n=='packages' else 0,name)
    return (0,name)
while stack:
    path,done=stack.pop()
    if done:
        if path!=root:
            parent=os.path.dirname(path); S[parent]+=S[path]; UNIQUE[parent]+=UNIQUE[path];N[parent]+=N[path]
        if os.path.dirname(path)==root:
            print(json.dumps({'completed':path,'seconds':round(time.time()-start,1),'files':files}),flush=True)
        continue
    try:
        ds=os.stat(path,follow_symlinks=False); dk=(ds.st_dev,ds.st_ino)
        if ds.st_ino and dk in seen_dirs:
            aliases[path]=seen_dirs[dk]; continue
        if ds.st_ino: seen_dirs[dk]=path
    except OSError as e:
        errors.append({'path':path,'error':str(e)[:150]});continue
    S[path]+=0;stack.append((path,True)); dirs=[]
    try:
        with os.scandir(path) as entries:
            for e in entries:
                try:
                    st=e.stat(follow_symlinks=False)
                    if getattr(st,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT:continue
                    if e.is_dir(follow_symlinks=False): dirs.append(e.path);continue
                    if not e.is_file(follow_symlinks=False):continue
                    n=st.st_size;S[path]+=n;N[path]+=1;files+=1
                    fs=os.stat(e.path,follow_symlinks=False);fk=(fs.st_dev,fs.st_ino)
                    if not fs.st_ino or fk not in seen_files:
                        UNIQUE[path]+=n
                        if fs.st_ino:seen_files.add(fk)
                    if path==root:root_files.append({'path':e.path,'bytes':n})
                except OSError as e2:errors.append({'path':e.path,'error':str(e2)[:150]})
    except OSError as e:errors.append({'path':path,'error':str(e)[:150]})
    dirs.sort(key=lambda p:priority(path,os.path.basename(p)),reverse=True)
    stack.extend((p,False) for p in dirs)
data={'sizes':dict(S),'unique_sizes':dict(UNIQUE),'counts':dict(N),'aliases':aliases,'errors':errors,
      'root_files':root_files,'files':files,'elapsed_seconds':round(time.time()-start,1)}
out=os.path.abspath(args.output)
os.makedirs(os.path.dirname(out), exist_ok=True)
with gzip.open(out,'wt',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,separators=(',',':'))
print(json.dumps({'report':out,'seconds':data['elapsed_seconds'],'files':files,'aliases':len(aliases),'errors':len(errors)}),flush=True)
