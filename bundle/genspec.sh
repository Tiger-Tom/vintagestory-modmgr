#!/bin/bash

# config
name="vintagestory-modmgr"
rootA="."; rootB="."
script="$rootB/main.py"; out="./specs/"
icon_win="$name.ico"; icon_mac="$name.icns"
oss=(lin win mac)

s="echo "

platform() {
    echo $( ($win && $s"windows") || ($mac && $s"macos") || ($lin && $s"linux") || $s"UNKNOWN" )
}
generate_name() {
    echo $name$($gui && $s"-gui")$($win && $s".exe")
}
generate_spec_name() {
    echo `platform`-$($gui && $s"avec" || $s"sans")_gui.spec
}

generate_spec() {
    lin=false; win=false; mac=false
    case "$1" in
        lin) lin=true ;;
        win) win=true ;;
        mac) mac=true ;;
    esac
    [ "$2" = "gui" ] && gui=true || gui=false
    name=`generate_name`
    args=(
        --onefile --specpath $out
        --name $name
        $($gui \
            && $s"--add-data $rootA/gui/:gui --windowed" \
            || $s"--hidden-import webview --console"  \
        )
        --splash ../bundle/vintagestory-modmgr_splash.png
        $($win || $s"--strip")
        $($gui && $s"--windowed" || $s"--console")
        $($lin || $s"--icon $rootA/bundle/vintagestory-modmgr_icon.ic$($win && $s"o" || $s"ns" )")
    )
    echo "${args[@]}"
    pyi-makespec "${args[@]}" $script
    mv $out/$name.spec $out/`generate_spec_name`
}

mkdir -p $out

for os in "${oss[@]}"; do
    generate_spec $os
    generate_spec $os gui
done