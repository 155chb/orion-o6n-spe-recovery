# Release 恢复与回退

## 适用范围

Orion O6N，测试 BIOS 1.2.4，Debian 13 arm64，GRUB/ACPI 启动。
先正常安装 Debian 到 SSD 并确认原版内核能启动，保留原版内核。
Release 为实验性 prerelease，包含旧已启动 Image、对应模块树和已验证
CPU_PM SPE 替换模块。v0.1.0 的 SPE 模块误用 XZ CRC64，内核报解压错误，
不能直接用于恢复；请使用修正为 CRC32 的 v0.1.1。修正不改变模块代码，
无需重新编译内核。完整下载、安装、启动与采样结果将分别记录。

## 校验和安装

下载 Release 的恢复 tar.gz 和同名 .sha256 文件：

```sh
sha256sum -c orion-o6n-spe-6.12.107-tested.tar.gz.sha256
tar -xzf orion-o6n-spe-6.12.107-tested.tar.gz
sudo python3 spe/tools/install-bundle.py orion-o6n-spe-6.12.107-tested
```

脚本核对内部 SHA256，拒绝覆盖已存在的同名内核/模块树，然后安装
Image/config/System.map、模块，执行 depmod 并生成本机 initramfs。
目录中的 build/source 链接和签名私钥不在恢复包内。
如果本机已安装同名实验内核，不要为了通过脚本检查直接删除它；先
选择原版内核并备份原文件，再根据实际情况处理。

## 生成 ACPI 描述与启动项

**必须先启动原版 Debian 且未启用任何 ACPI 覆写。** 从 uname -r 取得
当前 stock kernel 版本，再执行：

```sh
sudo python3 spe/tools/prepare-boot.py --stock-kernel "$(uname -r)"
```

脚本检查原始 MADT，自动取得本机 root UUID，生成单独的 SPE initrd
和 GRUB 项。不会修改 BIOS、EFI 启动顺序或固件表。只修改磁盘上的
GRUB 配置和 initramfs；默认仍是传入的 stock kernel。
若 BIOS/table 不同，脚本会停止，需重新核对 CPU UID 与 SPE PPI。

串口连接保持可用后单次启动：

```sh
sudo grub-reboot orion-spe-recovery-12
sudo reboot
```

启动后：

```sh
uname -r
cat /sys/devices/system/cpu/online
sudo modprobe arm_spe_pmu
cat /sys/bus/event_source/devices/arm_spe_0/cpumask
```

预期 kernel=6.12.107-spe-hetero，online=0-11，SPE mask=0-1,6-11。
先在确认过的单个 A720 上测试，再执行多核验证。不要对 A520 发起 SPE。

## 回退

单次启动失败时重新进入 GRUB，选择原版 Debian kernel；stock default
不变，下一次普通启动走 stock 项。需要通过串口查看早期错误时，使用
115200/8N1/无流控并保留终端日志。串口无需 DHCP。
SSH 地址在重启后可能变化，重新扫描实际活跃地址，不能沿用旧缓存。

确认已处于 stock 内核后，如要移除本工具生成的实验入口，只删除
对应的 49_orion_spe_recovery12、98-orion-spe-stock.cfg 和
initrd.img-6.12.107-spe-hetero-orion-spe12，再执行 update-grub。
不要删除 stock kernel/initrd。旧开发工作区中的 41–45 系列 GRUB 文件
来自历史实验，名称不同；本工具不会替你清理它们。

恢复包不包含用户密码、SSH key、GitHub token、machine-id 或本机 UUID。

## XZ 模块打包要求

该配置启用了内核模块解压，XZ 模块必须按内核构建规则使用 CRC32。
系统 xz 和 Python lzma 的默认 CRC64 会导致内核打印
decompression failed with status 6，即使 SHA256 和 vermagic 正确。

优先使用 modules_install 的原始输出。单独压缩替换模块时使用：

```sh
xz --check=crc32 -c arm_spe_pmu.ko > arm_spe_pmu.ko.xz
```

然后重新生成内部 SHA256SUMS 和外部包校验值；不能只修改已发布
压缩包却沿用旧校验文件。安装脚本现已在写入系统前拒绝 CRC64 SPE 模块。
