# SPDX-License-Identifier: GPL-2.0-only
import ctypes,os,threading,time,sys,json
BACKGROUND=len(sys.argv)>2 and sys.argv[2]=='background'
CPUS=(2,3,4,5) if BACKGROUND else (0,1,6,7,8,9,10,11)
BURST=sys.argv[1]=='burst'
MIXED=False
barrier=threading.Barrier(len(CPUS)+(4 if MIXED else 0))
libc=ctypes.CDLL(None)
libc.memmove.argtypes=(ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t)
libc.memmove.restype=ctypes.c_void_p
results=[];errors=[]
def worker(cpu,small=False):
 try:
  tid=threading.get_native_id();os.sched_setaffinity(tid,{cpu})
  n=(1 if small else 8)*1024*1024
  a=ctypes.create_string_buffer(n);b=ctypes.create_string_buffer(n)
  src=ctypes.addressof(a);dst=ctypes.addressof(b)
  barrier.wait(timeout=15)
  start=time.monotonic();end=start+(6 if BACKGROUND else 3);copies=0
  while time.monotonic()<end:
   for _ in range(8):libc.memmove(dst,src,n);src,dst=dst,src;copies+=1
   if BURST:time.sleep(0.04)
  results.append(dict(cpu=cpu,tid=tid,copies=copies,start=start,end=time.monotonic()))
 except BaseException as e:errors.append(str(e))
threads=[threading.Thread(target=worker,args=(c,)) for c in CPUS]
if MIXED:threads += [threading.Thread(target=worker,args=(c,True)) for c in (2,3,4,5)]
for t in threads:t.start()
for t in threads:t.join()
print(json.dumps(dict(workers=sorted(results,key=lambda x:x['cpu']),errors=errors)),flush=True)
if errors:sys.exit(1)
