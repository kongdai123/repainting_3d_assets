#!/usr/bin/env bash
set -e
set -x

nvidia-docker run \
    -it \
    --rm \
    -v /home/obukhova:/sl3a/dataset \
    second_life_3d_assets \
    "$@"
