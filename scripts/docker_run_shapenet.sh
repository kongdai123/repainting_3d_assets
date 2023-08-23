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

USE_CODE_FROM_DOCKER=0

if [ $# -lt 3 ]; then
    echo "Error: Insufficient command line arguments:"
    echo "$0 <path_dataset_shapenet> <path_outputs> [list_of_shapenet_model_ids]"
    exit 255
fi

REPAINTING3D_DATASET_ROOT="${1}"
shift

if [ ! -f "${REPAINTING3D_DATASET_ROOT}/.marker.dataset.shapenet.completed" ]; then
    echo "Invalid dataset path: ${REPAINTING3D_DATASET_ROOT}. Use script/setup_dataset_shapenet.sh to download it first."
    exit 255
fi

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

REPAINTING3D_OUT_SHAPENET="${1}"
shift

mkdir -p "${REPAINTING3D_OUT_SHAPENET}"

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
    --user $(id -u):$(id -g) \
    --ulimit core=0:0 \
    repainting_3d_assets \
    bash /repainting_3d_assets/code/scripts/conda_run_shapenet.sh /repainting_3d_assets "$@"
