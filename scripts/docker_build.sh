#!/usr/bin/env bash
set -e
set -x

if ! type source > /dev/null 2>&1; then
    echo "Restarting the script with bash interpreter"
    bash "$0" "$@"
    exit $?
fi
SELF=$(readlink -f "${BASH_SOURCE[0]}")
SELF_DIR=$(dirname "${SELF}")
SL3A_CODE_ROOT=$(realpath "${SELF_DIR}/..")

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
  --tag second_life_3d_assets \
  -f "${SELF_DIR}/Dockerfile" \
  "${SL3A_CODE_ROOT}"
