#!/usr/bin/env bash
set -e
if [ ! -z "${DEBUG}" ]; then
    set -x
fi

if ! type source > /dev/null 2>&1; then
    if [ ! -z "${DEBUG}" ]; then
        echo "Restarting the script with bash interpreter"
    fi
    bash "$0" "$@"
    exit $?
fi
SELF=$(readlink -f "${BASH_SOURCE[0]}")
SELF_DIR=$(dirname "${SELF}")
REPAINTING3D_CODE_ROOT=$(realpath "${SELF_DIR}/..")

DOCKER=""

if command -v nvidia-docker &> /dev/null; then
    DOCKER="nvidia-docker"
elif command -v docker &> /dev/null; then
    DOCKER="docker"
elif command -v podman &> /dev/null; then
    DOCKER="podman"
else
    echo "Error: No suitable Docker binary (docker, nvidia-docker, or podman) found in PATH."
    exit 255
fi

"${DOCKER}" build \
  --pull \
  --tag repainting_3d_assets \
  -f "${SELF_DIR}/Dockerfile" \
  "${REPAINTING3D_CODE_ROOT}"
