#!fontforge --lang=py -script

# 2つのフォントを合成する

import configparser
import math
import os
import shutil
import sys
import uuid

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
NERD_FONTS_STR = settings.get("DEFAULT", "NERD_FONTS_STR")
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
nerd_font = None


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
        elif arg == "--nerd-fonts":
            options["nerd-fonts"] = True
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

    # 合成前のグリフ調整
    src_font, dst_font = pre_composition_glyph_adjustment(src_font, dst_font)

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

    # GSUB、GPOSテーブル調整
    remove_lookups(src_font, remove_gsub=True, remove_gpos=True)

    # Nerd Fontのグリフを追加する
    if options.get("nerd-fonts"):
        add_nerd_font_glyphs(src_font, dst_font)

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
    variant += NERD_FONTS_STR if options.get("nerd-fonts") else ""

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


def pre_composition_glyph_adjustment(src_font, dst_font):
    """dst_font側のグリフを削除する。これにより合成時にsrc_font側のグリフが優先される"""
    # U+0000
    clear_glyph_range(dst_font, 0x0000, 0x0000)
    # 全角ASCII
    clear_glyph_range(dst_font, 0xFF01, 0xFF5E)
    # カギ括弧 「」
    clear_glyph_range(dst_font, 0xFF62, 0xFF63)
    # 日本語頻出の約もの
    clear_glyph_range(dst_font, 0x3001, 0x3015)
    # 中点
    clear_glyph_range(dst_font, 0x30FB, 0x30FB)
    # WAVE DASH, FULLWIDTH TILDE
    src_font = copy_altuni(src_font, (0x301C,))

    return src_font, dst_font


def clear_glyph_range(font, start: int, end: int):
    """グリフを削除する"""
    for i in range(start, end + 1):
        for glyph in font.selection.select(("ranges", None), i).byGlyphs:
            glyph.clear()
    font.selection.none()


def copy_altuni(font, unicode_list):
    for unicode in unicode_list:
        glyph = font[unicode]
        if glyph.altuni is not None:
            # 以下形式のタプルで返ってくる
            # (unicode-value, variation-selector, reserved-field)
            # 第3フィールドは常に0なので無視
            altunis = glyph.altuni

            # variation-selectorがなく (-1)、透過的にグリフを参照しているものは実体のグリフに変換する
            before_altuni = ""
            for altuni in altunis:
                # 直前のaltuniと同じ場合はスキップ
                if altuni[1] == -1 and before_altuni != ",".join(map(str, altuni)):
                    glyph.altuni = None
                    copy_target_unicode = altuni[0]
                    try:
                        copy_target_glyph = font.createChar(
                            copy_target_unicode,
                            f"uni{hex(copy_target_unicode).replace('0x', '').upper()}copy",
                        )
                    except Exception:
                        copy_target_glyph = font[copy_target_unicode]
                    copy_target_glyph.clear()
                    copy_target_glyph.width = glyph.width
                    font.selection.select(glyph.glyphname)
                    font.copy()
                    font.selection.select(copy_target_glyph.glyphname)
                    font.paste()
                before_altuni = ",".join(map(str, altuni))
    # エンコーディングの整理のため、開き直す
    font_path = f"{BUILD_FONTS_DIR}/{font.fullname}_{uuid.uuid4()}.ttf"
    font.generate(font_path)
    font.close()
    reopen_font = fontforge.open(font_path)
    # 一時ファイルを削除
    os.remove(font_path)
    return reopen_font


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


def remove_lookups(font, remove_gsub=True, remove_gpos=True):
    """GSUB, GPOSテーブルを削除する"""
    if remove_gsub:
        for lookup in font.gsub_lookups:
            font.removeLookup(lookup)
    if remove_gpos:
        for lookup in font.gpos_lookups:
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


def add_nerd_font_glyphs(jp_font, eng_font):
    """Nerd Fontのグリフを追加する"""
    global nerd_font
    # Nerd Fontのグリフを追加する
    if nerd_font is None:
        nerd_font = fontforge.open(f"{SOURCE_FONTS_DIR}/SymbolsNerdFont-Regular.ttf")
        nerd_font.em = EM_ASCENT + EM_DESCENT
        glyph_names = set()
        for nerd_glyph in nerd_font.glyphs():
            # Nerd Fontsのグリフ名をユニークにするため接尾辞を付ける
            nerd_glyph.glyphname = f"{nerd_glyph.glyphname}-nf"
            # postテーブルでのグリフ名重複対策
            # fonttools merge で合成した後、MacOSで `'post'テーブルの使用性` エラーが発生することへの対処
            if nerd_glyph.glyphname in glyph_names:
                nerd_glyph.glyphname = f"{nerd_glyph.glyphname}-{nerd_glyph.encoding}"
            glyph_names.add(nerd_glyph.glyphname)
            # 幅を調整する
            half_width = eng_font[0x0030].width
            # Powerline Symbols の調整
            if 0xE0B0 <= nerd_glyph.unicode <= 0xE0D4:
                # なぜかズレている右付きグリフの個別調整 (EM 1000 に変更した後を想定して調整)
                original_width = nerd_glyph.width
                if nerd_glyph.unicode == 0xE0B2:
                    nerd_glyph.transform(psMat.translate(-353, 0))
                elif nerd_glyph.unicode == 0xE0B6:
                    nerd_glyph.transform(psMat.translate(-414, 0))
                elif nerd_glyph.unicode == 0xE0C5:
                    nerd_glyph.transform(psMat.translate(-137, 0))
                elif nerd_glyph.unicode == 0xE0C7:
                    nerd_glyph.transform(psMat.translate(-214, 0))
                elif nerd_glyph.unicode == 0xE0D4:
                    nerd_glyph.transform(psMat.translate(-314, 0))
                nerd_glyph.width = original_width
                # 位置と幅合わせ
                if nerd_glyph.width < half_width:
                    nerd_glyph.transform(
                        psMat.translate((half_width - nerd_glyph.width) / 2, 0)
                    )
                elif nerd_glyph.width > half_width:
                    nerd_glyph.transform(psMat.scale(half_width / nerd_glyph.width, 1))
                # グリフの高さ・位置を調整する
                nerd_glyph.transform(psMat.scale(1, 1.14))
                nerd_glyph.transform(psMat.translate(0, 21))
            elif nerd_glyph.width < (EM_ASCENT + EM_DESCENT) * 0.6:
                # 幅が狭いグリフは中央寄せとみなして調整する
                nerd_glyph.transform(
                    psMat.translate((half_width - nerd_glyph.width) / 2, 0)
                )
            # 幅を設定
            nerd_glyph.width = half_width
    # 日本語フォントにマージするため、既に存在する場合は削除する
    for nerd_glyph in nerd_font.glyphs():
        if nerd_glyph.unicode != -1:
            # 既に存在する場合は削除する
            try:
                for glyph in jp_font.selection.select(
                    ("unicode", None), nerd_glyph.unicode
                ).byGlyphs:
                    glyph.clear()
            except Exception:
                pass
            try:
                for glyph in eng_font.selection.select(
                    ("unicode", None), nerd_glyph.unicode
                ).byGlyphs:
                    glyph.clear()
            except Exception:
                pass

    jp_font.mergeFonts(nerd_font)

    jp_font.selection.none()
    eng_font.selection.none()


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
