#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Install an extracted and SHA256-verified release bundle into unused paths."""
import argparse,os,shutil,subprocess,lzma
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('bundle',type=Path);a=p.parse_args()
b=a.bundle.resolve();k='6.12.107-spe-hetero'
if os.geteuid()!=0:raise SystemExit('Run as root')
subprocess.run(['sha256sum','-c','SHA256SUMS'],cwd=b,check=True)
mods=Path('/lib/modules')/k
files=[(b/'boot'/name,Path('/boot')/name) for name in ['vmlinuz-'+k,'config-'+k,'System.map-'+k]]
if mods.exists() or any(dst.exists() for _,dst in files):raise SystemExit('Kernel paths already exist; refusing to replace a running/tested installation')
if not (b/'lib/modules'/k).is_dir():raise SystemExit('Module tree missing')
candidates=[f for f in (b/'lib/modules'/k/'kernel/drivers/perf').glob('arm_spe_pmu.ko*') if f.name in {'arm_spe_pmu.ko','arm_spe_pmu.ko.xz','arm_spe_pmu.ko.gz','arm_spe_pmu.ko.zst'}]
if len(candidates)!=1:raise SystemExit('Expected exactly one SPE module')
if candidates[0].suffix=='.xz':
 decoder=lzma.LZMADecompressor()
 decoder.decompress(candidates[0].read_bytes())
 if decoder.check!=lzma.CHECK_CRC32:raise SystemExit('XZ module must use CRC32 for the tested kernel decompressor; do not use the default CRC64')
ver=subprocess.check_output(['modinfo','-F','vermagic',str(candidates[0])],text=True).split()[0]
if ver!=k:raise SystemExit('Module release mismatch')
shutil.copytree(b/'lib/modules'/k,mods,symlinks=True)
for src,dst in files:shutil.copy2(src,dst);dst.chmod(0o644)
subprocess.run(['depmod',k],check=True)
subprocess.run(['update-initramfs','-c','-k',k],check=True)
print('Installed kernel and fixed modules. Generate a local ACPI override next; no default boot selection was changed.')
