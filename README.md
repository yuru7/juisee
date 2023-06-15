# Juisee

Juisee は、欧文フォント JuliaMono と日本語フォント LINE Seed JP を合成したプログラミング向けフォントです。

👉 [ダウンロード](https://github.com/yuru7/juisee/releases)
※「Assets」内の zip ファイルをダウンロードしてご利用ください。

## 特徴

以下のような特徴があります。

- Unicode 文字の網羅性の高さが特徴的な [JuliaMono](https://juliamono.netlify.app) 由来のはんなりとした印象の英数字
- LINEの利便性とフレンドリーなアイデンティティから着想を得て制作された [LINE Seed](https://seed.line.me/index_jp.html) 由来のやわらかな印象の日本語文字
- 文字幅の比率 半角3:全角5 と、ゆとりのある幅の半角英数字
- 主に `->` `=>` などの矢印表現において JuliaMono 由来のリガチャを搭載

## サンプル

![image](https://github.com/yuru7/juisee/assets/13458509/68354be6-8fbf-4fb3-a8db-db43e24f83d3)
![image](https://github.com/yuru7/juisee/assets/13458509/6515d3c9-4141-4206-9ab3-ec8f2d8ab449)

## ビルド

**Windows**

```sh
& "C:\Program Files (x86)\FontForgeBuilds\bin\fontforge.exe" --lang=py -script .\fontforge_script.py && Get-ChildItem .\build\fontforge_Juisee*.ttf | % { python3 -m ttfautohint --dehint $_.FullName $_.FullName } && python3 fonttools_script.py
```

## ライセンス

SIL Open Font License, Version 1.1 が適用され、個人・商用問わず利用可能です。
