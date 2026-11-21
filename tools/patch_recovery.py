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

GUI_VOLD_INCLUDES_OLD = (
    '        "external/freetype/include",\n'
    '        "external/libpng"\n'
    '\n'
    '    ],'
)
GUI_VOLD_INCLUDES_NEW = (
    '        "external/freetype/include",\n'
    '        "external/libpng",\n'
    '        "system/vold"\n'
    '\n'
    '    ],'
)

RECOVERY_INCLUDES_OLD = "LOCAL_C_INCLUDES += system/vold \\\n\n"
RECOVERY_INCLUDES_NEW = (
    "LOCAL_C_INCLUDES += system/vold \\\n"
    "    system/update_engine\n\n"
)

KEYSTORE_CALL_OLD = "android::keystore::copySqliteDb();"
KEYSTORE_CALL_NEW = "android::keystore::syncKeystoreDb();"

TWRPAPP_REQUIRED_LINES = (
    "    me.twrp.twrpapp.apk \\\n"
    "    privapp-permissions-twrpapp.xml \\\n"
)

CHECKFORAPP_ANCHOR = "\tif (Is_TWRP_App_In_System()) {\n"
CHECKFORAPP_GUARD = (
    "\tif (!TWFunc::Path_Exists(\"/system/bin/me.twrp.twrpapp.apk\")) {\n"
    "\t\tLOGINFO(\"TWRP app not included in this build\\n\");\n"
    "\t\tDataManager::SetValue(\"tw_app_install_status\", 2);\n"
    "\t\treturn;\n"
    "\t}\n"
)

OZIP_DEFAULT_ANCHOR = "TW_X_OFFSET ?= 0\n"
OZIP_LIST_ANCHOR = "    tw_use_key_code_touch_sync \\\n"
OZIP_ASSIGN_ANCHOR = (
    "SOONG_CONFIG_twrpGlobalVars_tw_use_key_code_touch_sync := "
    "$(call twrp_scalar,$(TW_USE_KEY_CODE_TOUCH_SYNC))\n"
)
OZIP_VALUE_ANCHOR = '        "tw_delay_touch_init_ms",\n'
OZIP_BLOCK_ANCHOR = (
    '        tw_delay_touch_init_ms: {\n'
    '            cflags: ["-DTW_DELAY_TOUCH_INIT_MS=%s"]\n'
    '        },\n'
)
OZIP_BLOCK_ADDITION = (
    '        tw_ozip_decrypt_key: {\n'
    '            cflags: ["-DTW_OZIP_DECRYPT_KEY=\\"%s\\""]\n'
    '        },\n'
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


def patch_exclude_twrpapp(root):
    makefile = root / "bootable/recovery/Android.mk"
    text = makefile.read_text()
    if TWRPAPP_REQUIRED_LINES in text:
        makefile.write_text(text.replace(TWRPAPP_REQUIRED_LINES, "", 1))
        print("recovery: drop TWRP app prebuilts")
    elif "me.twrp.twrpapp.apk" in text:
        raise SystemExit(f"{makefile}: TWRP app 行布局与预期不符")
    else:
        print("recovery TWRP app already dropped")

    functions = root / "bootable/recovery/twrp-functions.cpp"
    text = functions.read_text()
    if 'TWRP app not included in this build' in text:
        print("checkforapp TWRP app guard already patched")
        return
    if text.count(CHECKFORAPP_ANCHOR) != 1:
        raise SystemExit(f"{functions}: 未找到唯一的 checkforapp 锚点")
    functions.write_text(text.replace(CHECKFORAPP_ANCHOR, CHECKFORAPP_GUARD + CHECKFORAPP_ANCHOR, 1))
    print("checkforapp: skip prompt when TWRP app absent")


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


def patch_gui_vold_includes(root):
    path = root / "bootable/recovery/gui/Android.bp"
    text = path.read_text()
    if '"system/vold"' in text:
        print("gui vold includes already patched")
        return
    if text.count(GUI_VOLD_INCLUDES_OLD) != 1:
        raise SystemExit(f"{path}: 未找到 libguitwrp include_dirs 锚点")
    path.write_text(text.replace(GUI_VOLD_INCLUDES_OLD, GUI_VOLD_INCLUDES_NEW))
    print("libguitwrp += system/vold include dir")


def patch_ozip_decrypt_key(root):
    makefile = root / "vendor/twrp/config/BoardConfigSoong.mk"
    text = makefile.read_text()
    if "TW_OZIP_DECRYPT_KEY ?=" not in text:
        text = text.replace(
            OZIP_DEFAULT_ANCHOR,
            "TW_OZIP_DECRYPT_KEY ?= 0\n" + OZIP_DEFAULT_ANCHOR,
            1,
        )
        text = text.replace(
            OZIP_LIST_ANCHOR,
            OZIP_LIST_ANCHOR + "    tw_ozip_decrypt_key \\\n",
            1,
        )
        text = text.replace(
            OZIP_ASSIGN_ANCHOR,
            OZIP_ASSIGN_ANCHOR
            + 'SOONG_CONFIG_twrpGlobalVars_tw_ozip_decrypt_key := '
            '$(subst \",, $(TW_OZIP_DECRYPT_KEY))\n',
            1,
        )
        makefile.write_text(text)
        print("twrpGlobalVars += tw_ozip_decrypt_key")
    else:
        print("twrpGlobalVars ozip key already patched")

    soong = root / "vendor/twrp/build/soong/Android.bp"
    text = soong.read_text()
    if '"tw_ozip_decrypt_key"' in text:
        print("twrp_defaults ozip key already patched")
        return
    if text.count(OZIP_VALUE_ANCHOR) != 1 or text.count(OZIP_BLOCK_ANCHOR) != 1:
        raise SystemExit(f"{soong}: 未找到 tw_delay_touch_init_ms 锚点")
    text = text.replace(
        OZIP_VALUE_ANCHOR,
        OZIP_VALUE_ANCHOR + '        "tw_ozip_decrypt_key",\n',
        1,
    )
    text = text.replace(OZIP_BLOCK_ANCHOR, OZIP_BLOCK_ANCHOR + OZIP_BLOCK_ADDITION, 1)
    soong.write_text(text)
    print("twrp_defaults += -DTW_OZIP_DECRYPT_KEY")


def patch_twrp_keystore_sync(root):
    path = root / "bootable/recovery/twrp.cpp"
    text = path.read_text()
    if KEYSTORE_CALL_NEW in text:
        print("twrp keystore sync already patched")
        return
    if text.count(KEYSTORE_CALL_OLD) != 1:
        raise SystemExit(f"{path}: 未找到唯一的 copySqliteDb 调用")
    path.write_text(text.replace(KEYSTORE_CALL_OLD, KEYSTORE_CALL_NEW))
    print("twrp.cpp copySqliteDb -> syncKeystoreDb")


def patch_recovery_update_engine_includes(root):
    path = root / "bootable/recovery/Android.mk"
    text = path.read_text()
    if "system/update_engine\n" in text:
        print("recovery update_engine includes already patched")
        return
    if text.count(RECOVERY_INCLUDES_OLD) != 1:
        raise SystemExit(f"{path}: 未找到唯一的 system/vold include 行")
    path.write_text(text.replace(RECOVERY_INCLUDES_OLD, RECOVERY_INCLUDES_NEW))
    print("recovery LOCAL_C_INCLUDES += system/update_engine")


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
    patch_gui_vold_includes(root)
    patch_ozip_decrypt_key(root)
    patch_twrp_keystore_sync(root)
    patch_recovery_update_engine_includes(root)
    patch_exclude_twrpapp(root)


if __name__ == "__main__":
    main()
