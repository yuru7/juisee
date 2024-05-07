#!/bin/env python3

import configparser
import glob
import os
import xml.etree.ElementTree as ET

import fontTools.ttx

# iniファイルを読み込む
settings = configparser.ConfigParser()
settings.read("build.ini", encoding="utf-8")

FONT_NAME = settings.get("DEFAULT", "FONT_NAME")
INPUT_PREFIX = settings.get("DEFAULT", "FONTFORGE_PREFIX")
OUTPUT_PREFIX = settings.get("DEFAULT", "FONTTOOLS_PREFIX")
BUILD_FONTS_DIR = settings.get("DEFAULT", "BUILD_FONTS_DIR")
HALF_WIDTH_STR = settings.get("DEFAULT", "HALF_WIDTH_STR")
HALF_WIDTH_12 = int(settings.get("DEFAULT", "HALF_WIDTH_12"))
FULL_WIDTH_35 = int(settings.get("DEFAULT", "FULL_WIDTH_35"))

xml_cmap = None


def main():
    global xml_cmap
    fix_font_tables("Regular")
    fix_font_tables("Bold")
    xml_cmap = None
    fix_font_tables("RegularItalic")
    fix_font_tables("BoldItalic")

    # 一時ファイルを削除
    # スタイル部分はワイルドカードで指定
    for filename in glob.glob(f"{BUILD_FONTS_DIR}/{OUTPUT_PREFIX}{FONT_NAME}*"):
        os.remove(filename)
    for filename in glob.glob(f"{BUILD_FONTS_DIR}/{INPUT_PREFIX}{FONT_NAME}*"):
        os.remove(filename)


def fix_font_tables(style):
    """フォントテーブルを編集する"""

    global xml_cmap

    # ファイルをパターンで指定
    filenames = glob.glob(f"{BUILD_FONTS_DIR}/{INPUT_PREFIX}{FONT_NAME}*-{style}.ttf")
    # ファイルが見つからない or 複数見つかった場合はエラー
    if len(filenames) == 0:
        print(f"Error: {INPUT_PREFIX}{FONT_NAME}*-{style}.ttf not found")
        return
    elif len(filenames) > 1:
        print(f"Error: {INPUT_PREFIX}{FONT_NAME}*-{style}.ttf is not unique")
        return
    filename = (
        filenames[0]
        .replace(f"{BUILD_FONTS_DIR}\\", "")
        .replace(f"{BUILD_FONTS_DIR}/", "")
    )
    # ファイル名から variant を取得
    variant = filename.replace(f"{INPUT_PREFIX}{FONT_NAME}", "").replace(
        f"-{style}.ttf", ""
    )

    # OS/2, post テーブルのみのttxファイルを出力
    xml = dump_ttx(style, variant)
    # OS/2 テーブルを編集
    fix_os2_table(xml, style, flag_hw=HALF_WIDTH_STR in variant)
    # post テーブルを編集
    fix_post_table(xml)

    # 処理が重いので初回だけ実行して結果をキャッシュする
    if xml_cmap is None:
        # cmap テーブルのみのttxファイルを出力
        xml_cmap = dump_ttx_cmap(style, variant)
        # cmap テーブルを編集
        fix_cmap_table(xml_cmap)

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


def dump_ttx(style: str, variant: str) -> ET:
    """OS/2, post テーブルのみのttxファイルを出力"""
    fontTools.ttx.main(
        [
            "-t",
            "OS/2",
            "-t",
            "post",
            "-f",
            "-o",
            f"{BUILD_FONTS_DIR}/{OUTPUT_PREFIX}{FONT_NAME}{variant}-{style}.ttx",
            f"{BUILD_FONTS_DIR}/{INPUT_PREFIX}{FONT_NAME}{variant}-{style}.ttf",
        ]
    )

    return ET.parse(
        f"{BUILD_FONTS_DIR}/{OUTPUT_PREFIX}{FONT_NAME}{variant}-{style}.ttx"
    )


def dump_ttx_cmap(style: str, variant: str) -> ET:
    """cmap テーブルのみのttxファイルを出力"""
    fontTools.ttx.main(
        [
            "-t",
            "cmap",
            "-f",
            "-o",
            f"{BUILD_FONTS_DIR}/{OUTPUT_PREFIX}{FONT_NAME}{variant}-{style}_cmap.ttx",
            f"{BUILD_FONTS_DIR}/{INPUT_PREFIX}{FONT_NAME}{variant}-{style}.ttf",
        ]
    )

    return ET.parse(
        f"{BUILD_FONTS_DIR}/{OUTPUT_PREFIX}{FONT_NAME}{variant}-{style}_cmap.ttx"
    )


def fix_os2_table(xml: ET, style: str, flag_hw: bool = False):
    """OS/2 テーブルを編集する"""
    # xAvgCharWidthを編集
    # タグ形式: <xAvgCharWidth value="1000"/>
    if flag_hw:
        x_avg_char_width = HALF_WIDTH_12
    else:
        x_avg_char_width = FULL_WIDTH_35
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
                # "#" で始まる行はコメント扱い
                if line.startswith("#"):
                    continue
                sub = ET.SubElement(elem, "map")
                sub.set("code", line.split(",")[0])
                sub.set("name", line.split(",")[1])
    for elem in xml.iter("cmap_format_12"):
        with open("add_cmap.csv", "r") as f:
            for line in f:
                # "#" で始まる行はコメント扱い
                if line.startswith("#"):
                    continue
                sub = ET.SubElement(elem, "map")
                sub.set("code", line.split(",")[0])
                sub.set("name", line.split(",")[1])


if __name__ == "__main__":
    main()
