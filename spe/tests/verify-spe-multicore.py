# SPDX-License-Identifier: GPL-2.0-only
import json,os,re,subprocess,time
from pathlib import Path
BASE=Path(__file__).resolve().parent
MODULE=Path(os.environ['SPE_MODULE']).resolve()
CPUS=(0,1,6,7,8,9,10,11);MASK='0-1,6-11'
OUT=Path(os.environ.get('SPE_OUTPUT_DIR', '/var/tmp'))/('cpu-pm-multicore-'+time.strftime('%Y%m%d-%H%M%S'));OUT.mkdir()
ROOT=Path('/sys/kernel/tracing');TR=ROOT/'instances/spe_multicore'
rows=[];original={str(p):p.read_text().strip() for c in CPUS for p in Path(f'/sys/devices/system/cpu/cpu{c}/cpuidle').glob('state*/disable')}
def run(cmd,**kw):return subprocess.run(cmd,check=True,**kw)
def put(p,v):p.write_text(str(v))
def usage():return {str(c):{p.parent.name:int(p.read_text()) for p in Path(f'/sys/devices/system/cpu/cpu{c}/cpuidle').glob('state*/usage')} for c in CPUS}
def sample(mode,kind,tag,mixed=False):
 before=usage();data=OUT/(tag+'.data')
 cmd=['perf','record','-e','arm_spe_0/load_filter=1,store_filter=1,min_latency=0/u','-c','20000','-o',str(data)]
 if mode=='system':cmd[2:2]=['-a','-C',MASK]
 cmd+=['--','taskset','-c',MASK,'python3',str(BASE/'spe-multicore-workload.py'),kind]
 bg=None
 if mixed:
  bg=subprocess.Popen(['taskset','-c','2-5','python3',str(BASE/'spe-multicore-workload.py'),'busy','background'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 if mode=='task':cmd=['taskset','-c',MASK]+cmd
 put(TR/'tracing_on',0);put(TR/'trace','');put(TR/'tracing_on',1)
 try:r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=35)
 finally:
  put(TR/'tracing_on',0)
  if bg is not None:
   bg.terminate();bg.wait(timeout=5)
 (OUT/(tag+'.record.log')).write_text(r.stdout)
 trace=(TR/'trace').read_text();(OUT/(tag+'.ftrace')).write_text(trace)
 after=usage();counts={str(c):0 for c in CPUS};unexpected={};samples=0
 with (OUT/(tag+'.decoded')).open('w') as f,(OUT/(tag+'.decode.log')).open('w') as err:
  d=subprocess.Popen(['perf','script','--itrace=M','-i',str(data)],stdout=subprocess.PIPE,stderr=err,text=True)
  for line in d.stdout:
   f.write(line)
   if 'memory:' not in line:continue
   m=re.search(r'\[(\d+)\]',line)
   if not m:raise RuntimeError('Cannot parse sample CPU')
   cpu=str(int(m[1]));samples+=1
   if cpu in counts:counts[cpu]+=1
   else:unexpected[cpu]=unexpected.get(cpu,0)+1
  dc=d.wait(timeout=20)
 row=dict(case=tag,mode=mode,workload=kind,mixed=mixed,record_exit=r.returncode,decode_exit=dc,total_samples=samples,per_cpu=counts,unexpected_cpus=unexpected,idle_delta={c:{s:after[c][s]-before[c][s] for s in before[c]} for c in before},command=cmd,trace_complete=[s for s in trace.splitlines() if 'entries-in-buffer/' in s])
 rows.append(row);(OUT/'results.json').write_text(json.dumps(rows,indent=2))
 print(json.dumps({k:row[k] for k in ('case','record_exit','decode_exit','total_samples','per_cpu','unexpected_cpus')}),flush=True)
 if r.returncode or dc or unexpected or any(v==0 for v in counts.values()):raise RuntimeError('Multicore verification failed: '+tag)
 time.sleep(1)
try:
 assert os.geteuid()==0 and os.uname().release=='6.12.107-spe-hetero'
 assert subprocess.check_output(['modinfo','-F','vermagic',str(MODULE)],text=True).split()[0]==os.uname().release
 assert Path('/sys/devices/system/cpu/online').read_text().strip()=='0-11'
 run(['modprobe','-r','arm_spe_pmu'])
 run(['insmod',str(MODULE),'spe_diag=0'])
 assert Path('/sys/bus/event_source/devices/arm_spe_0/cpumask').read_text().strip()==MASK
 TR.mkdir();put(TR/'tracing_on',0);put(TR/'buffer_size_kb',4096);put(TR/'tracing_cpumask','fc3');put(TR/'trace_clock','mono')
 put(TR/'set_ftrace_filter','arm_spe_cpu_pm_notify\narm_spe_pmu_start\narm_spe_pmu_stop\n')
 put(TR/'current_tracer','function');put(TR/'events/power/cpu_idle/enable',1)
 (OUT/'environment.json').write_text(json.dumps(dict(kernel=os.uname().release,online='0-11',spe_cpus=MASK,diag_logging=False,idle_original=original),indent=2))
 print('Results directory: '+str(OUT),flush=True)
 for n in (1,2):
  for kind in ('busy','burst'):
   for mode in ('system','task'):sample(mode,kind,f'{mode}-{kind}-{n}')
 for mode in ('system','task'):sample(mode,'burst',mode+'-burst-mixed',True)
finally:
 if TR.exists():
  put(TR/'tracing_on',0);put(TR/'events/enable',0);put(TR/'current_tracer','nop');os.rmdir(TR)
 subprocess.run(['modprobe','-r','arm_spe_pmu'],check=False)
 run(['modprobe','arm_spe_pmu'])
 (OUT/'cleanup.json').write_text(json.dumps(dict(idle_unchanged=all(Path(p).read_text().strip()==v for p,v in original.items()),installed_module_restored=True),indent=2))
print('COMPLETE '+str(OUT),flush=True)
