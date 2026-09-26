# Recorded validation (2026-09-26)

These are historical measurements, not predictions for another kernel or board.
All runs use Debian 6.12.107-spe-hetero and the three patch stages above.
The unpatched comparison uses the same diagnostic barriers, without CPU_PM handling.

| CPU6 test | Without CPU_PM (two runs) | With CPU_PM (two runs) |
| --- | --- | --- |
| System busy | 0 / 0 | 71980 / 73126 |
| Task busy | 78293 / 82827 | 54822 / 53592 |
| System burst | 0 / 0 | 6945 / 6883 |
| Task burst | 6743 / 5967 | 6301 / 5703 |

The multicore results contain 10 cases. All eight A720 CPUs produced nonzero
memory samples in every case. record/decode exit statuses were zero and no
unexpected sampled CPUs were found. Busy and burst workloads were tested in
both system and task mode, including separate A520 background workers.
Background workers were outside the inherited task-mode recording tree.
Their full completion counts were not recorded, so this is not proof of their
throughput. CPU idle counters increased; idle states were not disabled.

Function traces for system-burst-2 showed paired power-related start/stop counts
on CPUs 0,1,6,7,8,9,10,11: 208,63,70,52,65,62,66,65.
The CPU idle trace entry precedes the CPU_PM_ENTER callback: an active event at
that trace marker does not mean it remained enabled during actual powerdown.
No kernel WARN/Oops/panic was observed in these short tests. Long-term stability,
suspend/resume, CPU hotplug and simultaneous competing perf clients were not
established by this matrix.

The installed pre-CPU_PM module was restored after validation. Test files keep
compact results and cleanup status; large perf data and decoded traces are not
tracked in Git. Source/config/module hashes are in ../../config/provenance.json.
