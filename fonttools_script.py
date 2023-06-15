#!/bin/env python3

import glob
import fontTools.ttx
import xml.etree.ElementTree as ET
import os

FONT_NAME = "Juisee"
INPUT_PREFIX = "fontforge_"
OUTPUT_PREFIX = "fonttools_"

BUILD_FONTS_DIR = "build"

xml_cmap = None


def main():
    global xml_cmap
    fix_font_tables("Regular", False)
    fix_font_tables("Bold", False)
    xml_cmap = None
    fix_font_tables("RegularItalic", False)
    fix_font_tables("BoldItalic", False)

    # 一時ファイルを削除
    # スタイル部分はワイルドカードで指定
    for filename in glob.glob(f"{BUILD_FONTS_DIR}/{OUTPUT_PREFIX}{FONT_NAME}*"):
        os.remove(filename)
    for filename in glob.glob(f"{BUILD_FONTS_DIR}/{INPUT_PREFIX}{FONT_NAME}*"):
        os.remove(filename)


def fix_font_tables(style, flag_hw=False):
    """フォントテーブルを編集する"""

    global xml_cmap

    # OS/2, post テーブルのみのttxファイルを出力
    xml = dump_ttx(style)
    # OS/2 テーブルを編集
    fix_os2_table(xml, style, flag_hw)
    # post テーブルを編集
    fix_post_table(xml)

    # 処理が重いので初回だけ実行して結果をキャッシュする
    if xml_cmap is None:
        # cmap テーブルのみのttxファイルを出力
        xml_cmap = dump_ttx_cmap(style)
        # cmap テーブルを編集
        fix_cmap_table(xml_cmap)

    # 1:2版の場合の修飾子を追加する
    variant = "hw" if flag_hw else ""

    # ttxファイルを上書き保存
    xml.write(
        f"{BUILD_FONTS_DIR}/{OUTPUT_PREFIX}{FONT_NAME}{variant}-{style}.ttx",
        encoding="utf-8",
        xml_declaration=True,
    )
    xml_cmap.write(
        f"{BUILD_FONTS_DIR}/{OUTPUT_PREFIX}{FONT_NAME}{variant}-{style}_cmap.ttx",
        encoding="utf-8",
        xml_declaration=True,
    )

    # ttxファイルをttfファイルに適用
    fontTools.ttx.main(
        [
            "-o",
            f"{BUILD_FONTS_DIR}/{OUTPUT_PREFIX}{FONT_NAME}{variant}-{style}_os2_post.ttf",
            "-m",
            f"{BUILD_FONTS_DIR}/{INPUT_PREFIX}{FONT_NAME}{variant}-{style}.ttf",
            f"{BUILD_FONTS_DIR}/{OUTPUT_PREFIX}{FONT_NAME}{variant}-{style}.ttx",
        ]
    )
    fontTools.ttx.main(
        [
            "-o",
            f"{BUILD_FONTS_DIR}/{OUTPUT_PREFIX}{FONT_NAME}{variant}-{style}_os2_post_cmap.ttf",
            "-m",
            f"{BUILD_FONTS_DIR}/{OUTPUT_PREFIX}{FONT_NAME}{variant}-{style}_os2_post.ttf",
            f"{BUILD_FONTS_DIR}/{OUTPUT_PREFIX}{FONT_NAME}{variant}-{style}_cmap.ttx",
        ]
    )

    # ファイル名を変更
    os.rename(
        f"{BUILD_FONTS_DIR}/{OUTPUT_PREFIX}{FONT_NAME}{variant}-{style}_os2_post_cmap.ttf",
        f"{BUILD_FONTS_DIR}/{FONT_NAME}{variant}-{style}.ttf",
    )


def dump_ttx(style: str) -> ET:
    """OS/2, post テーブルのみのttxファイルを出力"""
    fontTools.ttx.main(
        [
            "-t",
            "OS/2",
            "-t",
            "post",
            "-f",
            "-o",
            f"{BUILD_FONTS_DIR}/{OUTPUT_PREFIX}{FONT_NAME}-{style}.ttx",
            f"{BUILD_FONTS_DIR}/{INPUT_PREFIX}{FONT_NAME}-{style}.ttf",
        ]
    )

    return ET.parse(f"{BUILD_FONTS_DIR}/{OUTPUT_PREFIX}{FONT_NAME}-{style}.ttx")


def dump_ttx_cmap(style: str) -> ET:
    """cmap テーブルのみのttxファイルを出力"""
    fontTools.ttx.main(
        [
            "-t",
            "cmap",
            "-f",
            "-o",
            f"{BUILD_FONTS_DIR}/{OUTPUT_PREFIX}{FONT_NAME}-{style}_cmap.ttx",
            f"{BUILD_FONTS_DIR}/{INPUT_PREFIX}{FONT_NAME}-{style}.ttf",
        ]
    )

    return ET.parse(f"{BUILD_FONTS_DIR}/{OUTPUT_PREFIX}{FONT_NAME}-{style}_cmap.ttx")


def fix_os2_table(xml: ET, style: str, flag_hw: bool = False):
    """OS/2 テーブルを編集する"""
    # xAvgCharWidthを編集
    # タグ形式: <xAvgCharWidth value="1000"/>
    if flag_hw:
        x_avg_char_width = 500
    else:
        x_avg_char_width = 1000
    for elem in xml.iter("xAvgCharWidth"):
        elem.set("value", str(x_avg_char_width))

    # fsSelectionを編集
    # タグ形式: <fsSelection value="00000000 11000000" />
    # スタイルに応じたビットを立てる
    if style == "Regular":
        fs_selection = "00000001 01000000"
    elif style == "RegularItalic":
        fs_selection = "00000001 00000001"
    elif style == "Bold":
        fs_selection = "00000001 00100000"
    elif style == "BoldItalic":
        fs_selection = "00000001 00100001"

    if fs_selection:
        for elem in xml.iter("fsSelection"):
            elem.set("value", fs_selection)

    # panoseを編集
    # タグ形式:
    # <panose>
    #   <bFamilyType value="2" />
    #   <bSerifStyle value="11" />
    #   <bWeight value="6" />
    #   <bProportion value="9" />
    #   <bContrast value="6" />
    #   <bStrokeVariation value="3" />
    #   <bArmStyle value="0" />
    #   <bLetterForm value="2" />
    #   <bMidline value="0" />
    #   <bXHeight value="4" />
    # </panose>
    if style == "Regular" or style == "Italic":
        bWeight = 5
    else:
        bWeight = 8
    if flag_hw:
        panose = {
            "bFamilyType": 2,
            "bSerifStyle": 11,
            "bWeight": bWeight,
            "bProportion": 9,
            "bContrast": 2,
            "bStrokeVariation": 2,
            "bArmStyle": 3,
            "bLetterForm": 2,
            "bMidline": 2,
            "bXHeight": 7,
        }
    else:
        panose = {
            "bFamilyType": 2,
            "bSerifStyle": 11,
            "bWeight": bWeight,
            "bProportion": 3,
            "bContrast": 2,
            "bStrokeVariation": 2,
            "bArmStyle": 3,
            "bLetterForm": 2,
            "bMidline": 2,
            "bXHeight": 7,
        }

    for key, value in panose.items():
        for elem in xml.iter(key):
            elem.set("value", str(value))


def fix_post_table(xml: ET):
    """post テーブルを編集する"""
    # isFixedPitchを編集
    # タグ形式: <isFixedPitch value="0"/>
    is_fixed_pitch = 0
    for elem in xml.iter("isFixedPitch"):
        elem.set("value", str(is_fixed_pitch))


def fix_cmap_table(xml: ET):
    """cmap テーブルを編集する"""
    # cmap_format_4, cmap_format_12 タグ内の末尾に add_cmap.csv の内容を追加
    # add_cmap.csv の内容は以下の形式
    # code,name,description
    for elem in xml.iter("cmap_format_4"):
        with open("add_cmap.csv", "r") as f:
            for line in f:
                sub = ET.SubElement(elem, "map")
                sub.set("code", line.split(",")[0])
                sub.set("name", line.split(",")[1])
    for elem in xml.iter("cmap_format_12"):
        with open("add_cmap.csv", "r") as f:
            for line in f:
                sub = ET.SubElement(elem, "map")
                sub.set("code", line.split(",")[0])
                sub.set("name", line.split(",")[1])


if __name__ == "__main__":
    main()
