#!/usr/bin/env bash
set -e
set -x

DOCKER=""

if command -v docker &> /dev/null; then
    DOCKER="docker"
elif command -v nvidia-docker &> /dev/null; then
    DOCKER="nvidia-docker"
elif command -v podman &> /dev/null; then
    DOCKER="podman"
else
    echo "Error: No suitable Docker binary (docker, nvidia-docker, or podman) found in PATH."
    exit 255
fi

"${DOCKER}" run \
    -it \
    --rm \
    second_life_3d_assets \
    "$@"
