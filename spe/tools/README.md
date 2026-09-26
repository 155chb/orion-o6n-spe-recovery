# Tools

`rebuild.sh` extracts the SHA256-pinned, Debian-patched linux-source-6.12 archive
and applies the three additional repository patches. It uses a fresh build path
and never modifies the existing build or installed kernel. Four build jobs are
the default. The config enables module signing with a locally generated key;
the key is intentionally not in this repository. Binary reproducibility of
signatures, timestamps and build-user strings is not promised.

`install-bundle.py` verifies release checksums and installs into unused kernel
paths. It rebuilds the initramfs locally and refuses to overwrite an existing
kernel/module installation. If an installation fails partway, inspect the files
before retrying; it is not an atomic package-manager transaction.

`prepare-boot.py` must be run after booting an original Debian kernel without ACPI
overrides. It checks the known firmware MADT revision/length/UIDs, assigns GSIV21
only to the known A720 UIDs, recalculates the table checksum, and prepends a newc
ACPI archive to the local initramfs. Optional --eight-core disables A520 entries.
It does not modify PPTT for the patched kernel, and does not change firmware.
It detects the root UUID locally and keeps the supplied stock kernel as default.
Future BIOS/table layouts require review rather than blindly changing UIDs.

The bootloader entries and initramfs are per-machine generated configuration.
Do not distribute the previous machine's initrd or root UUID as a recovery image.
