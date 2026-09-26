#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
set -eu
REPO=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
WORK=${1:?Usage: rebuild.sh /absolute/new-work-directory [jobs]}
JOBS=${2:-4}
case "$WORK" in /*) ;; *) echo 'Use an absolute work path' >&2; exit 1;; esac
[ ! -e "$WORK" ] || { echo 'Work directory already exists; choose a new one' >&2; exit 1; }
TAR=/usr/src/linux-source-6.12.tar.xz
EXPECTED=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["sha256"]["source_tar"])' "$REPO/spe/config/provenance.json")
printf '%s  %s\n' "$EXPECTED" "$TAR" | sha256sum -c -
mkdir -p "$WORK/build"
tar -xf "$TAR" -C "$WORK"
SRC="$WORK/linux-source-6.12"
for p in arm-spe-acpi-supported-cpus arm-spe-cpu-pm arm-spe-diagnostic-readback; do
    patch --batch --fuzz=0 -p1 -d "$SRC" < "$REPO/debian/patches/bugfix/arm64/$p.patch"
done
cp "$REPO/spe/config/tested-arm64.config" "$WORK/build/.config"
make -C "$SRC" O="$WORK/build" CROSS_COMPILE_COMPAT=arm-linux-gnueabihf- olddefconfig
make -C "$SRC" O="$WORK/build" CROSS_COMPILE_COMPAT=arm-linux-gnueabihf- -j"$JOBS" Image modules
# Build products only: no installation, firmware changes or reboot.
printf 'Built in %s/build\n' "$WORK"
