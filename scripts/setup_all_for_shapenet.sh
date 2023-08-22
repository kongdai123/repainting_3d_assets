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

if [ $# -ne 1 ]; then
    echo "Error: Exactly one argument is required - path to the working directory"
    exit 255
fi

export REPAINTING3D_ROOT=$1

export REPAINTING3D_CONDA_ROOT="${REPAINTING3D_ROOT}/conda"
export REPAINTING3D_DATASET_ROOT="${REPAINTING3D_ROOT}/dataset"
export REPAINTING3D_INSTANTNGP_ROOT="${REPAINTING3D_ROOT}/instantngp"
export REPAINTING3D_BUILD_INSTALL_ROOT="${REPAINTING3D_ROOT}/tools"

export TRANSFORMERS_CACHE="${REPAINTING3D_ROOT}/hfcache"
export HF_DATASETS_CACHE="${REPAINTING3D_ROOT}/hfcache"
export HF_HOME="${REPAINTING3D_ROOT}/hfcache"

bash "${SELF_DIR}/setup_conda.sh"
bash "${SELF_DIR}/setup_instantngp.sh"
bash "${SELF_DIR}/setup_model_export.sh"

if [ -z "${DISABLE_SHAPENET}" ]; then
    bash "${SELF_DIR}/setup_dataset_shapenet.sh"
fi

echo "Setup is now complete; refer to README.md to learn how to start painting on 3D meshes"
