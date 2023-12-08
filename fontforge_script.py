#!fontforge --lang=py -script

# 2つのフォントを合成する

import configparser
import math
import os
import shutil
import sys

import fontforge
import psMat

# iniファイルを読み込む
settings = configparser.ConfigParser()
settings.read("build.ini", encoding="utf-8")

VERSION = settings.get("DEFAULT", "VERSION")
FONT_NAME = settings.get("DEFAULT", "FONT_NAME")
SRC_FONT = settings.get("DEFAULT", "SRC_FONT")
DST_FONT = settings.get("DEFAULT", "DST_FONT")
SOURCE_FONTS_DIR = settings.get("DEFAULT", "SOURCE_FONTS_DIR")
BUILD_FONTS_DIR = settings.get("DEFAULT", "BUILD_FONTS_DIR")
VENDER_NAME = settings.get("DEFAULT", "VENDER_NAME")
FONTFORGE_PREFIX = settings.get("DEFAULT", "FONTFORGE_PREFIX")
IDEOGRAPHIC_SPACE = settings.get("DEFAULT", "IDEOGRAPHIC_SPACE")
HALF_WIDTH_STR = settings.get("DEFAULT", "HALF_WIDTH_STR")
SLASHED_ZERO_STR = settings.get("DEFAULT", "SLASHED_ZERO_STR")
INVISIBLE_ZENKAKU_SPACE_STR = settings.get("DEFAULT", "INVISIBLE_ZENKAKU_SPACE_STR")
EM_ASCENT = int(settings.get("DEFAULT", "EM_ASCENT"))
EM_DESCENT = int(settings.get("DEFAULT", "EM_DESCENT"))
HALF_WIDTH_12 = int(settings.get("DEFAULT", "HALF_WIDTH_12"))
FULL_WIDTH_35 = int(settings.get("DEFAULT", "FULL_WIDTH_35"))
ENG_GLYPH_SCALE_12 = float(settings.get("DEFAULT", "ENG_GLYPH_SCALE_12"))

FONT_ASCENT = EM_ASCENT + 120
FONT_DESCENT = EM_DESCENT + 250

COPYRIGHT = """[LINE Seed]
LINE Seed is copyrighted material owned by LINE Corp. (https://seed.line.me/index_jp.html)

[JuliaMono]
Copyright (c) 2020 - 2023, cormullion (https://github.com/cormullion/juliamono)

[Juisee]
Copyright 2022 Yuko Otawara
"""  # noqa: E501

options = {}


def main():
    # オプション判定
    get_options()
    if options.get("unknown-option"):
        usage()
        return

    # buildディレクトリを作成する
    if os.path.exists(BUILD_FONTS_DIR):
        shutil.rmtree(BUILD_FONTS_DIR)
    os.mkdir(BUILD_FONTS_DIR)
    # regular スタイルを生成する
    generate_font("Rg", "Regular", "Regular")
    # bold スタイルを生成する
    generate_font("Bd", "Bold", "Bold")
    # regular italic スタイルを生成する
    generate_font("Rg", "RegularItalic", "RegularItalic", italic=True)
    # bold italic スタイルを生成する
    generate_font("Bd", "BoldItalic", "BoldItalic", italic=True)


def usage():
    print(
        f"Usage: {sys.argv[0]} "
        "[--slashed-zero] [--invisible-zenkaku-space] [--half-width]"
    )


def get_options():
    """オプションを取得する"""

    global options

    # オプションなしの場合は何もしない
    if len(sys.argv) == 1:
        return

    for arg in sys.argv[1:]:
        # オプション判定
        if arg == "--slashed-zero":
            options["slashed-zero"] = True
        elif arg == "--invisible-zenkaku-space":
            options["invisible-zenkaku-space"] = True
        elif arg == "--half-width":
            options["half-width"] = True
        else:
            options["unknown-option"] = True
            return


def generate_font(src_style, dst_style, merged_style, italic=False):
    print(f"=== Generate {merged_style} style ===")

    # 合成するフォントを開く
    src_font, dst_font = open_fonts(src_style, dst_style)

    # フォントのEMを1000に変換する
    # src_font は既に1000なので dst_font のみ変換する
    em_1000(dst_font)

    # 合成に邪魔なグリフを削除する
    delete_unwanted_glyphs(dst_font)

    # 重複するグリフを削除する
    delete_duplicate_glyphs(src_font, dst_font)

    # 日本語グリフの斜体を生成する
    if italic:
        transform_italic_glyphs(src_font)

    # スラッシュ付きゼロ
    if options.get("slashed-zero"):
        slashed_zero(dst_font)

    # 3:5幅版との差分を調整する
    if options.get("half-width"):
        # 1:2 幅にする
        transform_half_width(src_font, dst_font)
    else:
        # src_fontで半角幅(500)のグリフの幅を3:5になるよう調整する
        width_500_to_600(src_font)

    # GSUBテーブルを削除する (ひらがな等の全角文字が含まれる行でリガチャが解除される対策)
    remove_lookups(src_font)

    # 合成する
    dst_font.mergeFonts(src_font)

    # 全角スペースを可視化する
    if not options.get("invisible-zenkaku-space"):
        visualize_zenkaku_space(dst_font)

    # オプション毎の修飾子を追加する
    variant = HALF_WIDTH_STR if options.get("half-width") else ""
    variant += SLASHED_ZERO_STR if options.get("slashed-zero") else ""
    variant += (
        INVISIBLE_ZENKAKU_SPACE_STR if options.get("invisible-zenkaku-space") else ""
    )

    # メタデータを編集する
    edit_meta_data(dst_font, merged_style, variant)

    # ttfファイルに保存
    dst_font.generate(
        f"{BUILD_FONTS_DIR}/{FONTFORGE_PREFIX}{FONT_NAME}{variant}-{merged_style}.ttf"
    )

    # ttfを閉じる
    src_font.close()
    dst_font.close()


def open_fonts(style_src: str, style_dst: str):
    return fontforge.open(
        f"{SOURCE_FONTS_DIR}/{SRC_FONT}{style_src}.ttf"
    ), fontforge.open(f"{SOURCE_FONTS_DIR}/{DST_FONT}{style_dst}.ttf")


def em_1000(font):
    """フォントのEMを1000に変換する"""
    em_size = EM_ASCENT + EM_DESCENT
    font.em = em_size


def delete_unwanted_glyphs(font):
    """dst_font側のグリフを削除する。これにより合成時にsrc_font側のグリフが優先される"""
    # U+0000
    clear_glyph_range(font, 0x0000, 0x0000)
    # U+FF01-FF5D
    clear_glyph_range(font, 0xFF01, 0xFF5D)
    # U+FF62-FF63
    clear_glyph_range(font, 0xFF62, 0xFF63)
    # U+3001-3015
    clear_glyph_range(font, 0x3001, 0x3015)
    # U+FF0D
    clear_glyph_range(font, 0xFF0D, 0xFF0D)


def clear_glyph_range(font, start: int, end: int):
    """グリフを削除する"""
    for i in range(start, end + 1):
        for glyph in font.selection.select(("ranges", None), i).byGlyphs:
            glyph.clear()
    font.selection.none()


def delete_duplicate_glyphs(src_font, dst_font):
    """src_fontとdst_fontのグリフを比較し、重複するグリフを削除する"""
    for glyph in src_font.glyphs():
        if glyph.unicode > 0:
            dst_font.selection.select(("more", "unicode"), glyph.unicode)
    for glyph in dst_font.selection.byGlyphs:
        if glyph.isWorthOutputting():
            src_font.selection.select(("more", "unicode"), glyph.unicode)
    for glyph in src_font.selection.byGlyphs:
        glyph.clear()
    src_font.selection.none()
    dst_font.selection.none()


def remove_lookups(font):
    """GSUB, GPOSテーブルを削除する"""
    for lookup in list(font.gsub_lookups) + list(font.gpos_lookups):
        font.removeLookup(lookup)


def transform_italic_glyphs(font):
    # 斜体の傾き
    ITALIC_SLOPE = 9
    # 傾きを設定する
    font.italicangle = -ITALIC_SLOPE
    # 全グリフを斜体に変換
    for glyph in font.glyphs():
        glyph.transform(psMat.skew(ITALIC_SLOPE * math.pi / 180))


def slashed_zero(font):
    # "zero.zero" を "zero" にコピーする
    font.selection.select("zero.zero")
    font.copy()
    font.selection.select(("unicode", None), 0x0030)
    font.paste()
    font.selection.none()


def width_500_to_600(font):
    """幅が500のグリフを600に変更する"""
    for glyph in font.glyphs():
        if glyph.width == 500:
            # グリフ位置を50右にずらしてから幅を600にする
            glyph.transform(psMat.translate(50, 0))
            glyph.width = 600


def transform_half_width(jp_font, eng_font):
    """1:2幅になるように変換する"""
    for glyph in eng_font.selection.select(("unicode", None), 0x0030).byGlyphs:
        before_width_eng = glyph.width
    after_width_eng = HALF_WIDTH_12
    for glyph in eng_font.glyphs():
        if glyph.width == before_width_eng:
            # 縮小
            glyph.transform(psMat.scale(ENG_GLYPH_SCALE_12, 1))
            # グリフ位置を調整してから幅を設定
            glyph.transform(psMat.translate(-(glyph.width - after_width_eng) / 2, 0))
            glyph.width = after_width_eng

    for glyph in jp_font.selection.select(("unicode", None), 0x3042).byGlyphs:
        before_half_width_jp = glyph.width / 2
        before_full_width_jp = glyph.width
    after_width_jp = HALF_WIDTH_12 * 2
    for glyph in jp_font.glyphs():
        if glyph.width == before_half_width_jp:
            # 英数字グリフと同じ幅にする
            glyph.transform(psMat.translate(-(glyph.width - after_width_eng) / 2, 0))
            glyph.width = after_width_eng
        elif glyph.width == before_full_width_jp:
            # グリフ位置を調整してから幅を設定
            glyph.transform(psMat.translate(-(glyph.width - after_width_jp) / 2, 0))
            glyph.width = after_width_jp


def visualize_zenkaku_space(font):
    """全角スペースを可視化する"""
    font.selection.select(("unicode", None), 0x3000)
    for glyph in font.selection.byGlyphs:
        glyph.clear()
    font.selection.none()
    font.mergeFonts(fontforge.open(f"{SOURCE_FONTS_DIR}/{IDEOGRAPHIC_SPACE}"))


def edit_meta_data(font, weight: str, variant: str):
    """フォント内のメタデータを編集する"""
    font.ascent = EM_ASCENT
    font.descent = EM_DESCENT
    font.os2_typoascent = EM_ASCENT
    font.os2_typodescent = -EM_DESCENT

    font.hhea_ascent = FONT_ASCENT
    font.hhea_descent = -FONT_DESCENT
    font.os2_winascent = FONT_ASCENT
    font.os2_windescent = FONT_DESCENT
    font.hhea_linegap = 0
    font.os2_typolinegap = 0

    # 一部ソフトで日本語表示ができなくなる事象への対策
    # なぜかJuliaMonoでは韓国語のビットが立っているので、それを除外し、代わりに日本語ビットを立てる
    font.os2_codepages = (0b1100000000000100000000111111111, 0)

    font.sfnt_names = (
        (
            "English (US)",
            "License",
            """This Font Software is licensed under the SIL Open Font License,
Version 1.1. This license is available with a FAQ
at: http://scripts.sil.org/OFL""",
        ),
        ("English (US)", "License URL", "http://scripts.sil.org/OFL"),
        ("English (US)", "Version", VERSION),
    )
    font.familyname = f"{FONT_NAME} {variant}".strip()
    font.fontname = f"{FONT_NAME}{variant}-{weight}"
    font.fullname = f"{FONT_NAME} {variant}".strip() + f" {weight}"
    font.os2_vendor = VENDER_NAME
    font.copyright = COPYRIGHT


if __name__ == "__main__":
    main()
