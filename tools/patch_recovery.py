#!/usr/bin/env python3
"""把 TB322FC recovery 分支里过时的 AOSP 假设改成当前源码的实际布局。

用法：patch_recovery.py <TWRP 源码根目录>
"""

import pathlib
import sys

MAGISK_PROBE_OLD = "$(wildcard external/magisk-prebuilt/Android.mk)"
MAGISK_PROBE_NEW = "$(wildcard external/magisk-prebuilt/prebuilt/Android.bp)"

LIBINSTALL_HEADER_OLD = '    header_libs: [\n        "libminadbd_headers",\n    ],'
LIBINSTALL_HEADER_NEW = (
    '    header_libs: [\n'
    '        "libminadbd_headers",\n'
    '        "libupdate_engine_headers",\n'
    '    ],'
)

MINUITWRP_ANCHOR = (
    '\tmatches, err := filepath.Glob("external/libdrm/Android.*")\n'
    '\t_ = matches\n'
    '\tif err == nil {\n'
    '\t\tcflags = append(cflags, "-DHAS_DRM")\n'
    '\t}\n'
)
MINUITWRP_ADDITION = (
    '\n'
    '\t// The Make build passes TW_BRIGHTNESS_PATH; the Soong port forwards only\n'
    '\t// the twrpGlobalVars typed config, so the fbdev backlight path was\n'
    '\t// compiled out and its blank parameter became unused.\n'
    '\tif brightnessPath := strings.TrimSpace(getMakeVars(ctx, "TW_BRIGHTNESS_PATH")); brightnessPath != "" {\n'
    '\t\tcflags = append(cflags, fmt.Sprintf("-DTW_BRIGHTNESS_PATH=%q", brightnessPath))\n'
    '\t}\n'
)


def patch_magisk_probe(root):
    path = root / "bootable/recovery/prebuilt/Android.mk"
    text = path.read_text()
    if MAGISK_PROBE_NEW in text:
        print("magisk probe already patched")
        return
    if MAGISK_PROBE_OLD not in text:
        raise SystemExit(f"{path}: 未找到 magisk 探针 {MAGISK_PROBE_OLD}")
    path.write_text(text.replace(MAGISK_PROBE_OLD, MAGISK_PROBE_NEW))
    print("magisk probe -> prebuilt/Android.bp")


def patch_libinstall_headers(root):
    path = root / "bootable/recovery/install/Android.bp"
    text = path.read_text()
    if '"libupdate_engine_headers"' in text:
        print("libinstall headers already patched")
        return
    if text.count(LIBINSTALL_HEADER_OLD) != 1:
        raise SystemExit(f"{path}: 未找到唯一的 libinstall header_libs 块")
    path.write_text(text.replace(LIBINSTALL_HEADER_OLD, LIBINSTALL_HEADER_NEW))
    print("libinstall += libupdate_engine_headers")


def patch_minuitwrp_brightness(root):
    path = root / "bootable/recovery/minuitwrp/libminuitwrp_defaults.go"
    text = path.read_text()
    if "-DTW_BRIGHTNESS_PATH=" in text:
        print("minuitwrp brightness path already patched")
        return
    if text.count(MINUITWRP_ANCHOR) != 1:
        raise SystemExit(f"{path}: 未找到 HAS_DRM 锚点")
    path.write_text(text.replace(MINUITWRP_ANCHOR, MINUITWRP_ANCHOR + MINUITWRP_ADDITION))
    print("minuitwrp += -DTW_BRIGHTNESS_PATH")


def check_prebuilt_exists(root):
    path = root / "external/magisk-prebuilt/prebuilt/Android.bp"
    if not path.is_file():
        raise SystemExit(f"{path} 不存在，magisk 预编译布局与预期不符")


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    root = pathlib.Path(sys.argv[1]).resolve()
    check_prebuilt_exists(root)
    patch_magisk_probe(root)
    patch_libinstall_headers(root)
    patch_minuitwrp_brightness(root)


if __name__ == "__main__":
    main()
