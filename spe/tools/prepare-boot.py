#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Generate an Orion O6N MADT override from original firmware tables."""
import argparse,os,struct,tempfile,subprocess,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--kernel',default='6.12.107-spe-hetero');p.add_argument('--stock-kernel',required=True);p.add_argument('--eight-core',action='store_true');a=p.parse_args()
if os.geteuid()!=0:raise SystemExit('Run as root from a stock ACPI boot without table overrides')
if any(ch not in '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.+_-' for ch in a.kernel+a.stock_kernel):raise SystemExit('Invalid kernel release')
k=a.kernel;stock=a.stock_kernel
for name in ['vmlinuz-'+k,'initrd.img-'+k,'vmlinuz-'+stock]:
 if not (Path('/boot')/name).is_file():raise SystemExit('Missing /boot/'+name)
d=bytearray(Path('/sys/firmware/acpi/tables/APIC').read_bytes());rev=struct.unpack_from('<I',d,24)[0]
if d[:4]!=b'APIC' or len(d)!=1064 or struct.unpack_from('<I',d,4)[0]!=len(d) or sum(d)%256 or rev!=16777473:raise SystemExit('Firmware MADT differs from tested BIOS 1.2.4; stop and review')
a720={0,1,6,7,8,9,10,11};a520={2,3,4,5};seen=set();i=44
while i<len(d):
 typ,n=d[i:i+2]
 if n<2 or i+n>len(d):raise SystemExit('Invalid MADT entry')
 if typ==11:
  if n<80:raise SystemExit('Short GICC entry')
  uid,flags=struct.unpack_from('<II',d,i+8);gsi=struct.unpack_from('<H',d,i+78)[0]
  if uid in seen or uid not in a720|a520 or not flags&1 or gsi:raise SystemExit('Need original firmware with 12 enabled CPUs and zero SPE GSIVs')
  seen.add(uid);struct.pack_into('<H',d,i+78,21 if uid in a720 else 0)
  if a.eight_core and uid in a520:struct.pack_into('<I',d,i+12,flags&~1)
 i+=n
if seen!=a720|a520:raise SystemExit('Unexpected CPU UID set')
struct.pack_into('<I',d,24,rev+1);d[9]=0;d[9]=(-sum(d))&255
uuid=subprocess.check_output(['findmnt','-no','UUID','/'],text=True).strip()
if not uuid or any(c not in '0123456789abcdefABCDEF-' for c in uuid):raise SystemExit('Unsupported root UUID')
mode='8' if a.eight_core else '12';bootid='orion-spe-recovery-'+mode
initrd=Path('/boot')/('initrd.img-'+k+'-orion-spe'+mode);entry=Path('/etc/grub.d')/('49_orion_spe_recovery'+mode);default=Path('/etc/default/grub.d/98-orion-spe-stock.cfg')
if initrd.exists() or entry.exists() or default.exists():raise SystemExit('Recovery boot files exist; refusing to overwrite them')
with tempfile.TemporaryDirectory() as tmp:
 table=Path(tmp)/'kernel/firmware/acpi/APIC.aml';table.parent.mkdir(parents=True);table.write_bytes(d)
 names=['kernel','kernel/firmware','kernel/firmware/acpi','kernel/firmware/acpi/APIC.aml']
 with initrd.open('xb') as f:
  subprocess.run(['cpio','-o','-H','newc','--quiet'],cwd=tmp,input=('\n'.join(names)+'\n').encode(),stdout=f,check=True)
  with (Path('/boot')/('initrd.img-'+k)).open('rb') as src:shutil.copyfileobj(src,f)
  f.flush();os.fsync(f.fileno())
initrd.chmod(0o644)
entry.write_text(f"""#!/bin/sh
exec tail -n +3 $0
menuentry 'Orion O6N SPE {mode}-core recovery test' --id {bootid} {{
 search --no-floppy --fs-uuid --set=root {uuid}
 linux /boot/vmlinuz-{k} root=UUID={uuid} ro rootwait loglevel=7 console=tty0 console=ttyAMA0,115200
 initrd /boot/{initrd.name}
}}
""");entry.chmod(0o755)
default.parent.mkdir(parents=True,exist_ok=True)
default.write_text(f'GRUB_DEFAULT="gnulinux-advanced-{uuid}>gnulinux-{stock}-advanced-{uuid}"\n')
subprocess.run(['update-grub'],check=True);subprocess.run(['grub-script-check','/boot/grub/grub.cfg'],check=True)
print('Prepared',bootid,'with local root UUID. Stock kernel remains default.')
print('For one test boot: sudo grub-reboot '+bootid+'; sudo reboot')
