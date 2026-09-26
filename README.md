# Radxa Orion O6N · Debian SPE 修复与恢复

这是以 Debian 官方内核打包 Git 历史为基础的实验性派生仓库。
目标：12 核保持在线，在 8 个 Cortex-A720 上使用 SPE，同时避免 A520
访问不支持的 SPE 寄存器，并处理 CPU 深层空闲后的 SPE 恢复。

## 来源

- Debian 官方仓库：https://salsa.debian.org/kernel-team/linux.git
- 基线标签：`debian/6.12.107-1`
- 基线提交：`1c8550dea793986605df31b61c1d0596d877c047`
- 源码包：`linux` / `6.12.107-1`，实验使用其 `linux-source-6.12` 归档。
- 实验内核：`6.12.107-spe-hetero`；硬件：Orion O6N，BIOS 1.2.4。

官方仓库主要保存 Debian 打包文件与 quilt 补丁。它不直接包含完整
Linux 源码。原有 Debian 历史和许可证信息保留；本仓库新增的驱动代码
以 `debian/patches/bugfix/arm64/arm-spe-*.patch` 提交并登记在 series 中。
这些修复尚未提交或合入 Debian/Linux 上游。

## 修复与当前状态

1. **ACPI 异构注册**：按 MADT GICC 的非零 SPE GSIV 生成 CPU 掩码。
   GSIV 为 0 的 CPU 不参与 SPE；不同的非零 GSIV 拒绝注册。
2. **CPU 电源管理**：进入上下文丢失空闲状态前停止采样、提交 AUX；
   返回或进入失败后复位寄存器，恢复此前正在运行的事件。
3. **可关闭诊断**：`spe_diag` 默认关闭；保留测试时加入的两处 ISB。

在本机 12 核在线、A720 为 CPU `0-1,6-11` 的条件下，10 项多核测试
全部得到非零样本。详细数据见 [验证记录](spe/results/2026-09-26/README.md)。
这不是长时间稳定性、热插拔或系统挂起恢复验证。

已测试的内核 Image 包含异构注册修复；CPU_PM 修复位于单独测试的
SPE 模块中。Release 恢复包将该模块放入对应模块树，源码和配置哈希
见 [provenance.json](spe/config/provenance.json)。当前开发板安装的模块
此前已在测试清理阶段恢复为 CPU_PM 修复前版本；本次备份操作没有
替换正在运行的内核或模块。

## 使用入口

- [问题、证据与机制](spe/docs/diagnosis.md)
- [源码和构建](spe/docs/build.md)
- [Release 安装与系统恢复](spe/docs/recovery.md)
- [测试方法](spe/tests/README.md)
- [恢复脚本](spe/tools/README.md)
- [许可证说明](spe/docs/licensing.md)

推荐先阅读恢复说明，保留原版内核，并用单次启动测试。
不需要修改固件。不能把本机 CPU 编号或 UID 映射套用到其他板卡。

## 已验证的二进制恢复包

[v0.1.1 Release](https://github.com/155chb/orion-o6n-spe-recovery/releases/tag/v0.1.1-debian6.12.107-spe)
已完成本机重新下载、校验、安装、启动、单核和十项多核 SPE 验证，
恢复时无需重新编译内核。步骤见 spe/docs/recovery.md，
证据见 spe/results/release-v0.1.1-20260926。旧 v0.1.0 有 XZ 模块压缩格式
错误，不应使用。仍为实验性 prerelease，长期稳定性尚未验证。
