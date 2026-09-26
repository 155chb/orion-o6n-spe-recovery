#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# Stage only; never install into the running system.
set -eu
WORK=${1:?Usage: bundle-build.sh /absolute/build-work /absolute/new-bundle}
DEST=${2:?Usage: bundle-build.sh /absolute/build-work /absolute/new-bundle}
case "$WORK:$DEST" in /*:/*) ;; *) echo 'Both paths must be absolute' >&2; exit 1;; esac
[ ! -e "$DEST" ] || { echo 'Bundle directory already exists' >&2; exit 1; }
SRC="$WORK/linux-source-6.12"
BUILD="$WORK/build"
K=$(cat "$BUILD/include/config/kernel.release")
[ "$K" = 6.12.107-spe-hetero ] || { echo 'Unexpected kernel release' >&2; exit 1; }
test -s "$BUILD/arch/arm64/boot/Image"
test -s "$BUILD/drivers/perf/arm_spe_pmu.ko"
mkdir -p "$DEST/boot"
make -C "$SRC" O="$BUILD" CROSS_COMPILE_COMPAT=arm-linux-gnueabihf- INSTALL_MOD_PATH="$DEST" INSTALL_MOD_STRIP=1 modules_install
rm -f "$DEST/lib/modules/$K/build" "$DEST/lib/modules/$K/source"
install -m 644 "$BUILD/arch/arm64/boot/Image" "$DEST/boot/vmlinuz-$K"
install -m 644 "$BUILD/.config" "$DEST/boot/config-$K"
install -m 644 "$BUILD/System.map" "$DEST/boot/System.map-$K"
cd "$DEST"
find boot lib -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum > SHA256SUMS
echo "Verified-build bundle staged at $DEST; installation and boot testing are still required."
