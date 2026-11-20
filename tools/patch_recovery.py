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


if __name__ == "__main__":
    main()
