#!/usr/bin/env bash
# Build the Moon72 ZMK firmware locally, without GitHub Actions.
# Uses the west workspace (zmk, zephyr, modules) already checked out for the
# KLOR in ~/zmk-config-klor and the zmk-build-arm docker image.
#
#   ./build.sh            left + right + settings_reset -> uf2/
#   ./build.sh left       one half
set -euo pipefail
cd "$(dirname "$0")"
WS=${ZMK_WORKSPACE:-$HOME/zmk-config-klor}
IMAGE=${ZMK_IMAGE:-zmkfirmware/zmk-build-arm:3.5}   # the image already pulled for the KLOR; builds Zephyr 4.1 fine
CFG=$PWD/zmk-config
mkdir -p uf2

build() {  # build <shield> [snippet]
    local extra=()
    [[ -n "${2:-}" ]] && extra=(-S "$2")
    echo "== $1"
    docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -e ZEPHYR_BASE=/workspace/zephyr \
        -v "$WS:/workspace" -v "$CFG:/cfg" -w /workspace "$IMAGE" \
        west build -p -s zmk/app -d "/cfg/build/$1" -b nice_nano//zmk "${extra[@]}" -- \
        -DSHIELD="$1" -DZMK_CONFIG=/cfg/config -DZephyr_DIR=/workspace/zephyr/share/zephyr-package/cmake
    cp "$CFG/build/$1/zephyr/zmk.uf2" "uf2/$1.uf2"
}

case "${1:-all}" in
    left)  build moon72_left studio-rpc-usb-uart ;;
    right) build moon72_right ;;
    all)   build moon72_left studio-rpc-usb-uart; build moon72_right; build settings_reset ;;
esac
ls -la uf2
