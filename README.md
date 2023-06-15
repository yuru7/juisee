# Juisee

Juisee は、欧文フォント JuliaMono と日本語フォント LINE Seed JP を合成したプログラミング向けフォントです。

## 特徴

以下のような特徴があります。

- Unicode 文字の網羅性の高さが特徴的な [JuliaMono](https://juliamono.netlify.app) 由来のはんなりとした印象の英数字
- LINEの利便性とフレンドリーなアイデンティティから着想を得て制作された [LINE Seed](https://seed.line.me/index_jp.html) 由来のやわらかな印象の日本語文字

## ビルド

**Windows**

```sh
& "C:\Program Files (x86)\FontForgeBuilds\bin\fontforge.exe" --lang=py -script .\fontforge_script.py
Get-ChildItem .\build\fontforge_Juisee*.ttf | % { python3 -m ttfautohint --dehint $_.FullName $_.FullName }
python3 fonttools_script.py
```

## ライセンス

SIL Open Font License, Version 1.1 が適用され、個人・商用問わず利用可能です。
