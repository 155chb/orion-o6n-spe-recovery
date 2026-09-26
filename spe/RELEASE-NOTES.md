# v0.1.0-debian6.12.107-spe (experimental prerelease)

Debian official baseline: debian/6.12.107-1 / 1c8550dea793986605df31b61c1d0596d877c047.
Contains per-CPU ACPI SPE registration, CPU_PM stop/reset/restart and optional
readback diagnostics. All 10 short multicore cases produced samples on all 8
A720 CPUs while 12 CPUs remained online.

Artifact: orion-o6n-spe-6.12.107-tested.tar.gz plus SHA256 file.
The previously booted kernel Image has the ACPI change. Its matching module tree
in this bundle replaces only arm_spe_pmu with the tested CPU_PM module. This
bundle composition has not had a separate cold-boot validation. Initramfs and
ACPI overrides must be generated on the target machine; no user keys or firmware
are included. See spe/docs/recovery.md before installation.

No long-term stability, suspend/resume or CPU-hotplug guarantee. Not an official
Debian package or official signed kernel. Driver/source/config hashes are recorded.
