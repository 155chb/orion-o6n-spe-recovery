# Multicore validation

The workload and validation runner originate from the successful 10-case matrix.
The runner now accepts the replacement module and output directory via environment
variables, instead of a user-specific workspace path. Only this path adaptation is
new; historical results describe the original run, not a rerun of these wrappers.

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
