#!/usr/bin/env bash
set -e
if ! type source > /dev/null 2>&1; then
    bash "$0" "$@"
    exit $?
fi
if [ ! -z "${DEBUG}" ]; then
    set -x
fi

SELF=$(readlink -f "${BASH_SOURCE[0]}")
SELF_DIR=$(dirname "${SELF}")

if [ $# -lt 1 -o $# -gt 2 ]; then
    echo "Error: Expecting one or two arguments: <project working directory path> [--with-shapenet]"
    exit 255
fi

export WORK_ROOT="$(readlink -f "$1")"

if [ -z "${REPAINTING3D_DO_NOT_MANAGE_HFCACHE}" ]; then
    export TRANSFORMERS_CACHE="${WORK_ROOT}/hfcache"
    export HF_DATASETS_CACHE="${WORK_ROOT}/hfcache"
    export HF_HOME="${WORK_ROOT}/hfcache"
fi

export REPAINTING3D_ENV_NAME=repainting_3d_assets
export REPAINTING3D_INSTANTNGP_ARCHS=${REPAINTING3D_INSTANTNGP_ARCHS:-"60 70 75 80 86"}

bash "${SELF_DIR}/install_conda.sh" "${WORK_ROOT}/conda" "${SELF_DIR}/environment.yml"

source "${WORK_ROOT}/conda/miniconda3/bin/activate" "${REPAINTING3D_ENV_NAME}"

bash "${SELF_DIR}/install_instantngp.sh" "${WORK_ROOT}/instantngp" "${SELF_DIR}/instant_ngp_patches" "${REPAINTING3D_INSTANTNGP_ARCHS}"
bash "${SELF_DIR}/install_model_export.sh" "${WORK_ROOT}/conda/miniconda3/envs/${REPAINTING3D_ENV_NAME}"
bash "${SELF_DIR}/install_draco.sh" "${WORK_ROOT}/conda/miniconda3/envs/${REPAINTING3D_ENV_NAME}"

if [ "$2" = "--with-shapenet" ]; then
    bash "${SELF_DIR}/install_dataset.sh" "${WORK_ROOT}/dataset"
fi

echo "Setup is now complete; refer to README.md to learn how to start painting on 3D meshes"
