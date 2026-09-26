# 问题与定位

## 1. 固件没有描述 SPE 中断

BIOS 1.2.4 原始 MADT 中 12 个 GICC 的 SPE GSIV 均为 0。
仅加载 arm_spe_pmu 模块不能凭空创建中断资源。本机通过 initramfs
ACPI table upgrade 提供修改后的 MADT：A720 UID 0、1、6–11 使用
GSIV21，A520 UID 2–5 保持 0。GSIV21 对应 GIC PPI5。
这是本机已验证的板级描述，不是跨平台自动探测算法。

## 2. 原版 ACPI SPE 注册要求同构

Debian 原版 6.12 注册逻辑检查所有可能 CPU 的 SPE 中断和 PPTT 异构 ID。
混合 A520/A720 时会拒绝注册。原版 8 核实验同时禁用了 A520，并调整
PPTT IDENTICAL 描述。该历史成功测试采用任务采样，不能作为原版系统
采样能跨深层空闲工作的证据。

新增 ACPI 代码单独处理 SPE，不改变 TRBE 的原有注册逻辑。
掩码来自 MADT，再与 PPI 分区掩码相交；驱动没有写死 0xFE1 或 CPU 编号。
该方案仍要求所选 SPE CPU 使用同一 PPI，并具有兼容 SPE 特性。

## 3. 全核掩码会触发不支持的寄存器访问

Sky1 Linux 曾把 PMU 公布为 CPUs 0-11。perf 在 CPU3（A520）开始事件时
出现 Undefined instruction，PC 位于 arm_spe_perf_aux_output_begin。
这解释了为什么 PMU 注册成功不能证明所有 CPU 都能进行 SPE 采样。
此次修复只允许支持掩码中的 CPU；CPU_PM 回调也首先检查掩码。

## 4. 系统采样与任务采样的区别

任务事件随调度切换调用 SPE stop/start，重新配置缓冲区与控制寄存器。
CPU-wide 事件在任务睡眠时仍可能保持活动。原驱动没有 CPU_PM 恢复，
CPU 进入上下文丢失空闲再返回时，读到异常 PMBPTR/PMSIRR/PMSFCR，
AUX 区域出现大段零，解码没有样本。

异常示例：写入 PMBPTR=ffff800088c04000，返回读到
1c4f5319e7834b8c；第一页非零检查为 0。禁用深层空闲后，指针、缓冲
内容和采样恢复正常。这支持 CPU 电源状态相关解释；尚未通过固件源
代码或硅级测量确定错误寄存器恢复的具体执行者。

修复仿照普通 ARM PMU 的 CPU_PM 生命周期：ENTER 时停止并结算 AUX，
EXIT/ENTER_FAILED 时复位再恢复先前运行的事件。选择直接回调方式以
匹配本版 6.12 API；旧版本的 RCU_NONIDLE 用法不适用此构建。

## 5. 验证边界

两轮 CPU6 系统 busy/burst 从 0 样本恢复为非零；任务模式也保持成功。
多核测试覆盖 busy/burst、系统/任务以及独立 A520 后台负载，所有 A720
都有样本且没有意外 CPU。深层空闲计数增加，没有永久关闭空闲状态。
函数跟踪显示功耗切换的 stop/start 成对发生。

CPU idle 入口 tracepoint 在 CPU_PM_ENTER 处理之前；不能根据入口标记
时的 event 状态判断硬件实际关电时仍在采样。
历史单核 results.json 中 start_calls/stop_calls 是宽松文本计数，可能
包括其他函数名，不能用作精确调用次数。精确机制结论使用函数跟踪的
独立行匹配；多核汇总见验证记录。样本数是实验结果，不是完整性证明。
