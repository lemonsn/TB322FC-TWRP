#!/usr/bin/env python3
"""校验 TWRP recovery.img 的 boot header 与 ramdisk，不依赖设备。"""

import argparse
import struct
import sys

ANDROID_MAGIC = b"ANDROID!"
LZ4_LEGACY_MAGIC = b"\x02\x21\x4c\x18"
LZ4_FRAME_MAGIC = b"\x04\x22\x4d\x18"


def fail(message):
    print(f"FAIL: {message}", file=sys.stderr)
    return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument("--partition-size", type=int, required=True)
    parser.add_argument("--expect-header-version", type=int, default=4)
    parser.add_argument("--expect-page-size", type=int, default=4096)
    parser.add_argument("--require-empty-kernel", action="store_true")
    args = parser.parse_args()

    with open(args.image, "rb") as image:
        header = image.read(4096)
        if len(header) < 44:
            return fail(f"{args.image} 小于 boot header 长度")
        if header[:8] != ANDROID_MAGIC:
            return fail(f"magic 为 {header[:8]!r}，不是 Android boot image")

        kernel_size = struct.unpack_from("<I", header, 8)[0]
        ramdisk_size = struct.unpack_from("<I", header, 12)[0]
        header_size = struct.unpack_from("<I", header, 20)[0]
        header_version = struct.unpack_from("<I", header, 40)[0]

        print(f"header_version={header_version} header_size={header_size}")
        print(f"kernel_size={kernel_size} ramdisk_size={ramdisk_size}")

        if header_version != args.expect_header_version:
            return fail(f"header_version 期望 {args.expect_header_version}")
        if args.require_empty_kernel and kernel_size != 0:
            return fail("recovery 应不含内核，但 kernel_size 非 0")
        if ramdisk_size == 0:
            return fail("ramdisk_size 为 0")

        ramdisk_offset = args.expect_page_size + kernel_size
        image.seek(ramdisk_offset)
        ramdisk_head = image.read(4)
        if ramdisk_head not in (LZ4_LEGACY_MAGIC, LZ4_FRAME_MAGIC):
            return fail(f"ramdisk 起始 {ramdisk_head!r} 不是 LZ4")
        print("ramdisk_compression=lz4")

        image.seek(0, 2)
        image_size = image.tell()
        print(f"image_bytes={image_size} partition_bytes={args.partition_size}")
        if image_size > args.partition_size:
            return fail("镜像超过 recovery 分区容量")

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
