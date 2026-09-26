# 构建

## Debian 官方打包工作流

本仓库保留 Debian 打包 Git 历史，新增驱动改动采用 DEP-3 风格 patch
并加入 `debian/patches/series`。参考：

- https://kernel-team.pages.debian.net/kernel-handbook/ch-common-tasks.html#s-common-dev
- https://kernel-team.pages.debian.net/kernel-handbook/ch-source.html
- 仓库内 `debian/README.source`

官方开发流程取得对应 upstream DFSG orig tar 后，用 `debian/rules orig`
应用 Debian quilt 栈；完整 Debian 包构建还需要官方 build-dependencies
和 flavour 配置。本仓库恢复脚本采用更小的 native Image/modules 路径，
读取已包含 Debian 补丁的 linux-source-6.12 归档，因此只应用三份新增
SPE 补丁，不能再次重复应用完整 Debian series。

## 重建已测试配置

在 ARM64 Debian 13 上准备依赖：

```sh
sudo apt update
sudo apt install git build-essential bc bison flex libssl-dev libelf-dev \
  dwarves rsync cpio kmod xz-utils python3 gcc-arm-linux-gnueabihf \
  linux-source-6.12=6.12.107-1
```

若该准确版本已不在当前镜像，使用 Debian 官方包归档/快照获取；不要
放宽源码 SHA256 校验后继续。具体归档哈希见 provenance.json。

```sh
git clone https://github.com/155chb/orion-o6n-spe-recovery.git
cd orion-o6n-spe-recovery
git switch spe/orion-o6n-6.12.107
./spe/tools/rebuild.sh /absolute/new-spe-build 4
```

脚本检查源码归档哈希，解包到新目录，应用三份补丁，复制实际测试的
config，然后执行 olddefconfig 和 Image/modules。输出在工作目录的
build 下，不安装、不重启。完整构建是长任务，应在独立命令会话中运行。

本次仓库整理验证了补丁重放后的两个驱动与测试工作区逐字节一致，
并检查 Python/shell 语法。没有再次执行完整内核重建；新的路径参数化
脚本不等于已经做过一次从零系统重建。

## 配置、签名和版本

kernelrelease 是 6.12.107-spe-hetero。CONFIG_CPU_PM=y、ARM_SPE_PMU=m、
MODVERSIONS=y；保存的 config 还包含 module signing 与 BTF 配置。
本机生成的签名私钥不会公开。新构建可生成自己的 key，因此不能期望
签名或完整二进制字节与旧产物完全相同。Secure Boot 下的信任与签名
需另行配置；不能把此手工构建称为 Debian 官方签名内核。

模块必须来自同一个完整构建并匹配 running kernel/version CRC。
在已准备的完整构建目录增量编译 SPE 模块使用：

```sh
make -C /absolute/new-spe-build/linux-source-6.12 \
  O=/absolute/new-spe-build/build CROSS_COMPILE_COMPAT=arm-linux-gnueabihf- \
  -j4 drivers/perf/arm_spe_pmu.ko
```

不要用 M=drivers/perf 替代，该方式会按外部模块路径处理。
本仓库 Release 是带校验的手工恢复包，不是 Debian 官方 .deb。
