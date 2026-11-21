# TB322FC TWRP

Lenovo Legion Y700 Gen4（TB322FC / elden）的 TWRP recovery 构建仓库。

- 设备：Lenovo Legion Y700 Gen4（TB322FC，社区代号 elden）
- Recovery：TWRP 3.7.1 / Android 16
- 分区：独立 `recovery_a` / `recovery_b`，每个 100 MiB
- 构建：GitHub Actions，无需本地 AOSP 环境

> 非官方 TWRP。刷机有风险，请自行确认 bootloader 状态、目标槽位并先备份现有 recovery。

## 仓库内容

- `device/lenovo/TB322FC/`：设备树，包含 fstab、twrp.flags、init 脚本、触摸固件和 recovery 侧 vendor 服务。
- `tools/patch_recovery.py`：对 AOSP 16 / recovery fork 的构建补丁。
- `tools/verify_recovery_image.py`：产物校验，检查 header、空内核、LZ4 ramdisk 和分区大小。
- `.github/workflows/build-twrp.yml`：GitHub Actions 构建流程。

## 构建

### GitHub Actions

1. Fork 本仓库。
2. 在 fork 的 Actions 页面启用 workflow。
3. 手动运行 `Build TWRP recovery for Y700 gen4 (TB322FC)`，或向 `main` 推送 `device/`、`tools/` 下的改动。
4. 构建完成后下载 artifact `twrp-recovery-TB322FC`。

构建只依赖公开仓库，不需要 secrets：

- `TWRP-Test/platform_manifest_twrp_aosp`，分支 `twrp-16.0`
- `lemonsn/android_bootable_recovery`，分支 `twrp-16.0-TB322FC`，commit 固定在 workflow 中

### 本地构建

```shell
mkdir twrp && cd twrp
repo init --depth=1 -u https://github.com/TWRP-Test/platform_manifest_twrp_aosp.git -b twrp-16.0
repo sync -c --no-tags --optimized-fetch --no-clone-bundle -j"$(nproc)"

(cd bootable/recovery
 git fetch https://github.com/lemonsn/android_bootable_recovery.git twrp-16.0-TB322FC
 git checkout -f FETCH_HEAD)

git clone --depth=1 https://github.com/lemonsn/TB322FC-TWRP.git /tmp/TB322FC-TWRP
mkdir -p device/lenovo
cp -a /tmp/TB322FC-TWRP/device/lenovo/TB322FC device/lenovo/TB322FC
python3 /tmp/TB322FC-TWRP/tools/patch_recovery.py .
```

```shell
export ALLOW_MISSING_DEPENDENCIES=true
source build/envsetup.sh
lunch twrp_TB322FC
m -j"$(nproc)" recoveryimage
```

产物在 `out/target/product/TB322FC/recovery.img`。

AOSP/TWRP 构建比较吃内存；资源有限时可以把 `-j"$(nproc)"` 改成 `-j3`，并准备 swap。

## 功能状态

已在真机确认：

- ADB
- 显示与触摸
- FBE 解密
- 振动

已编译包含，但未逐项完整验证：

- MTP
- fastbootd
- TWRP 内刷写与备份/恢复
- microSD / USB OTG（节点已配置，需要插卡或插 U 盘实测）

## 说明

- 镜像使用 AOSP testkey 签名，不是 Lenovo 官方密钥。官方 ZUXOS OTA 包不在 TWRP 的 `otacerts.zip` 信任范围内，不能用 TWRP 刷官方 OTA。
- 官方系统更新会更新目标槽的 recovery，可能覆盖 TWRP；更新后需要重新刷入。
- 本仓库构建不包含 TWRP App。镜像中的 `magiskboot` 只是 TWRP 的 boot 镜像重打包工具，不是 Magisk root 或管理器。
- recovery 镜像大小正好 100 MiB，只能刷到 `recovery_a` / `recovery_b`，不要刷到 boot 分区。

## 致谢

本仓库的设备树、构建补丁和验证流程建立在以下项目之上：

- [TWRP-Test / platform_manifest_twrp_aosp](https://github.com/TWRP-Test/platform_manifest_twrp_aosp)：Android 16 TWRP manifest。
- [polygraphene / android_device_lenovo_TB322FC](https://github.com/polygraphene/android_device_lenovo_TB322FC)：TB322FC 设备树上游。
- [polygraphene / android_bootable_recovery](https://github.com/polygraphene/android_bootable_recovery)：TB322FC recovery 分支。
- [turbo-boo / android_device_lenovo_TB322FC](https://github.com/turbo-boo/android_device_lenovo_TB322FC)：设备树参考与早期适配。
- [TWRP](https://twrp.me/)：Team Win Recovery Project。
- [kmiit / twrp_device_oplus_sm87xx](https://github.com/kmiit/twrp_device_oplus_sm87xx)：设备树结构参考。
- [YuKongA / twrp_device_xiaomi_sm8750_thales](https://github.com/YuKongA/twrp_device_xiaomi_sm8750_thales)：SM8750 设备树参考。
- [qualcomm / qdlrs](https://github.com/qualcomm/qdlrs)：EDL 刷写工具。

## License

GPL-3.0，见 [LICENSE](LICENSE)。
