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

USE_CODE_FROM_DOCKER=0

if [ $# -ne 3 ]; then
    echo "Error: Insufficient command line arguments:"
    echo "$0 <path_input> <path_output> <prompt>"
    exit 255
fi

PATH_IN=$(realpath "$1")
shift
PATH_OUT=$(realpath "$1")
shift
PROMPT="$1"
shift

PATH_IN_DIR=$(dirname "${PATH_IN}")
PATH_IN_FILE=$(basename "${PATH_IN}")
mkdir -p "${PATH_OUT}"

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

CMD_MOUNT_LATEST_CODE=""
if [ ! "${USE_CODE_FROM_DOCKER}" -eq "1" ]; then
    CMD_MOUNT_LATEST_CODE="-v "${SL3A_CODE_ROOT}":/sl3a/code"
fi

"${DOCKER}" run \
    -it \
    --rm \
    -v "${SL3A_DATASET_ROOT}":/sl3a/dataset \
    -v "${SL3A_OUT_SHAPENET}":/sl3a/out_shapenet \
    ${CMD_MOUNT_LATEST_CODE} \
    -v "${PATH_IN_DIR}":/sl3a/assets_in \
    -v "${PATH_OUT}":/sl3a/assets_out \
    --user $(id -u):$(id -g) \
    --ulimit core=0:0 \
    repainting_3d_assets \
    bash /sl3a/code/scripts/conda_run_userdata.sh \
        /sl3a \
        "/sl3a/assets_in/${PATH_IN_FILE}" \
        /sl3a/assets_out/ \
        "${PROMPT}"
