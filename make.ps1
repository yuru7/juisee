# ini から VERSION を取得
$ini = Get-Content .\build.ini
$version = ($ini | Select-String -Pattern "VERSION").ToString().Split("=")[1].Trim()

# スクリプトファイルがある場所に移動する
Set-Location -Path $PSScriptRoot
# 各ファイルを置くフォルダを作成
New-Item -ItemType Directory -Force -Path ".\release_files\"
# ビルドフォルダを削除
Remove-Item -Path .\build -Recurse -Force

$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$release_dir = ".\release_files\build_$timestamp\"
New-Item -ItemType Directory -Force -Path $release_dir
$move_dir_normal = "$release_dir\Juisee_$version"
New-Item -ItemType Directory -Force -Path $move_dir_normal
$move_dir_nf = "$release_dir\Juisee_NF_$version"
New-Item -ItemType Directory -Force -Path $move_dir_nf

# 通常版
& "C:\Program Files (x86)\FontForgeBuilds\bin\fontforge.exe" --lang=py -script .\fontforge_script.py `
    && Get-ChildItem .\build\fontforge_Juisee*.ttf | ForEach-Object { python -m ttfautohint --dehint --no-info $_.FullName $_.FullName } `
    && python fonttools_script.py `
    && Copy-Item -Path .\build\*.ttf -Destination $move_dir_normal -Force

    # 半角1:全角2版
& "C:\Program Files (x86)\FontForgeBuilds\bin\fontforge.exe" --lang=py -script .\fontforge_script.py --half-width `
    && Get-ChildItem .\build\fontforge_Juisee*.ttf | ForEach-Object { python -m ttfautohint --dehint --no-info $_.FullName $_.FullName } `
    && python fonttools_script.py `
    && Copy-Item -Path .\build\*.ttf -Destination $move_dir_normal -Force

    # 通常版 + Nerd Font
& "C:\Program Files (x86)\FontForgeBuilds\bin\fontforge.exe" --lang=py -script .\fontforge_script.py --nerd-fonts `
    && Get-ChildItem .\build\fontforge_Juisee*.ttf | ForEach-Object { python -m ttfautohint --dehint --no-info $_.FullName $_.FullName } `
    && python fonttools_script.py `
    && Copy-Item -Path .\build\*.ttf -Destination $move_dir_nf -Force

    # 半角1:全角2版 + Nerd Font
& "C:\Program Files (x86)\FontForgeBuilds\bin\fontforge.exe" --lang=py -script .\fontforge_script.py --half-width --nerd-fonts `
    && Get-ChildItem .\build\fontforge_Juisee*.ttf | ForEach-Object { python -m ttfautohint --dehint --no-info $_.FullName $_.FullName } `
    && python fonttools_script.py `
    && Copy-Item -Path .\build\*.ttf -Destination $move_dir_nf -Force
