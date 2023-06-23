# Juisee

Juisee は、欧文フォント [JuliaMono](https://juliamono.netlify.app) と日本語フォント [LINE Seed JP](https://seed.line.me/index_jp.html) を合成したプログラミング向けフォントです。

🥤 [DOWNLOAD](https://github.com/yuru7/juisee/releases) 🥤  
※「Assets」内の zip ファイルをダウンロードしてご利用ください。

![image](https://github.com/yuru7/juisee/assets/13458509/b7e3d2ba-12d0-42f2-8c72-bdc376048cc7)

## 特徴

以下のような特徴があります。

- Unicode 文字の網羅性の高さが特徴の [JuliaMono](https://juliamono.netlify.app) 由来の曲線的な英数字
- LINE の利便性とフレンドリーなアイデンティティから着想を得て制作された [LINE Seed JP](https://seed.line.me/index_jp.html) 由来のやわらかな印象の日本語文字
- 文字幅比率が 半角3:全角5、ゆとりのある幅の半角英数字
- 主に `->` `=>` などの矢印表現において JuliaMono 由来のリガチャを搭載

## サンプル

![image](https://github.com/yuru7/juisee/assets/13458509/68354be6-8fbf-4fb3-a8db-db43e24f83d3)
![image](https://github.com/yuru7/juisee/assets/13458509/6515d3c9-4141-4206-9ab3-ec8f2d8ab449)
![image](https://github.com/yuru7/juisee/assets/13458509/96522093-2cb2-4fe9-8094-764993c3e04f)

## ビルド

ビルドに使用するツール、ランタイム

- fontforge: `20230101` \[[Windows](https://fontforge.org/en-US/downloads/windows/)\] \[[Linux](https://fontforge.org/en-US/downloads/gnulinux/)\]
- Python: `>=3.8`

### Windows

```sh
# 必要パッケージのインストール
pip install -r requirements.txt
# ビルド
& "C:\Program Files (x86)\FontForgeBuilds\bin\fontforge.exe" --lang=py -script .\fontforge_script.py && Get-ChildItem .\build\fontforge_Juisee*.ttf | % { python -m ttfautohint --dehint --no-info $_.FullName $_.FullName } && python fonttools_script.py
```

`fontforge_script.py` オプション:

- `--slashed-zero` : `0` を斜線付きゼロにする
- `--invisible-zenkaku-space` : 全角スペースを不可視にする
- `--half-width` : 半角文字と全角文字の幅の比率を 半角1:全角2 にする

オプション付きの実行例:

```sh
& "C:\Program Files (x86)\FontForgeBuilds\bin\fontforge.exe" --lang=py -script .\fontforge_script.py --slashed-zero --invisible-zenkaku-space
```

### Linux

coming soon...

## ライセンス

SIL Open Font License, Version 1.1 が適用され、個人・商用問わず利用可能です。

ソースフォントのライセンスも同様に SIL Open Font License, Version 1.1 が適用されています。詳しくは `source` ディレクトリに含まれる `LICENSE_<FontName>` ファイルを参照してください。
