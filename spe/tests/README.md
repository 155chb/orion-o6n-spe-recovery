# Multicore validation

The workload and validation runner originate from the successful 10-case matrix.
The runner accepts the replacement module and output directory via environment
variables. On 2026-09-26 it was rerun successfully on a fresh GitHub-only full build,
after installing and booting that build. See spe/results/reproduction-20260926.
The runner temporarily loads the uncompressed build module; this can produce an
expected unsigned-module warning, then cleanup reloads the installed module.

Run on the custom 6.12.107-spe-hetero kernel with the MADT override active:

```sh
sudo env SPE_MODULE=/absolute/build/drivers/perf/arm_spe_pmu.ko \
  SPE_OUTPUT_DIR=/var/tmp python3 spe/tests/verify-spe-multicore.py
```

Requires perf, Python, taskset, tracefs mounted at /sys/kernel/tracing, root and
12 online CPUs with the Orion A720 mask 0-1,6-11. The module must match the running
kernel exactly. Do not substitute an all-CPU mask. The temporary replacement is
unloaded in the finally block and the installed module is reloaded. The runner
records whether idle settings stayed unchanged. Inspect cleanup.json after a
failure; forcibly terminating Python bypasses its finally cleanup.

No permanent power-state changes are made. Tests collect large .data/.decoded
files under SPE_OUTPUT_DIR; keep them out of Git. These runs take about one minute
on this board, not including a module build. Use an independent command session
if executing remotely.
