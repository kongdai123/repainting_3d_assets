#!/usr/bin/env bash
set -e
if [ ! -z "${DEBUG}" ]; then
    set -x
fi

if ! type source > /dev/null 2>&1; then
    bash "$0" "$@"
    exit $?
fi
SELF=$(readlink -f "${BASH_SOURCE[0]}")
SELF_DIR=$(dirname "${SELF}")
REPAINTING3D_CODE_ROOT=$(readlink -f "${SELF_DIR}/..")

USE_CODE_FROM_DOCKER=0

if [ $# -ne 3 ]; then
    echo "Error: Insufficient command line arguments:"
    echo "$0 <path_input> <path_output> <prompt>"
    exit 255
fi

PATH_IN="$(readlink -f "$1")"
shift
PATH_OUT="$(readlink -f "$1")"
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
    CMD_MOUNT_LATEST_CODE="-v "${REPAINTING3D_CODE_ROOT}":/repainting_3d_assets/code"
fi

"${DOCKER}" run \
    -it \
    --rm \
    -v "${REPAINTING3D_DATASET_ROOT}":/repainting_3d_assets/dataset \
    -v "${REPAINTING3D_OUT_SHAPENET}":/repainting_3d_assets/out_shapenet \
    ${CMD_MOUNT_LATEST_CODE} \
    -v "${PATH_IN_DIR}":/repainting_3d_assets/assets_in \
    -v "${PATH_OUT}":/repainting_3d_assets/assets_out \
    --user $(id -u):$(id -g) \
    --ulimit core=0:0 \
    repainting_3d_assets \
    bash /repainting_3d_assets/code/scripts/conda_run.sh \
        /repainting_3d_assets \
        "/repainting_3d_assets/assets_in/${PATH_IN_FILE}" \
        /repainting_3d_assets/assets_out/ \
        "${PROMPT}"
