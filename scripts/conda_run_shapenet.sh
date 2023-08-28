#!/usr/bin/env bash
set -e
if [ ! -z "${DEBUG}" ]; then
    set -x
fi

if [ $# -lt 2 ]; then
    echo "Error: Insufficient command line arguments:"
    echo "$0 <working_dir> [list_of_shapenet_model_ids]"
    exit 255
fi

if ! type source > /dev/null 2>&1; then
    bash "$0" "$@"
    exit $?
fi

if [ -n "$CONDA_PREFIX" ]; then
    echo "Deactivating Conda environment: $CONDA_PREFIX"
    conda deactivate
fi

REPAINTING3D_ENV_NAME=${REPAINTING3D_ENV_NAME:-repainting_3d_assets}

REPAINTING3D_ROOT="$(readlink -f "$1")"
shift

REPAINTING3D_CONDA_ROOT="${REPAINTING3D_ROOT}/conda"
if [ ! -f "${REPAINTING3D_CONDA_ROOT}/miniconda3/bin/conda" ]; then
    echo "\"conda\" not found, check setup_conda_bin.sh"
    exit 255
fi
source "${REPAINTING3D_CONDA_ROOT}/miniconda3/bin/activate" ${REPAINTING3D_ENV_NAME}

REPAINTING3D_DATASET_ROOT_DEFAULT="${REPAINTING3D_ROOT}/dataset"
REPAINTING3D_DATASET_ROOT="${REPAINTING3D_DATASET_ROOT:-${REPAINTING3D_DATASET_ROOT_DEFAULT}}"
if [ ! -f ${REPAINTING3D_DATASET_ROOT}/.marker.dataset.shapenet.completed ]; then
    echo "Dataset not found; re-run setup.sh as follows:"
    echo "bash scripts/setup.sh ${REPAINTING3D_ROOT} --with-shapenet"
    exit 0
fi

REPAINTING3D_INSTANTNGP_ROOT_DEFAULT="${REPAINTING3D_ROOT}/instantngp"
REPAINTING3D_INSTANTNGP_ROOT="${REPAINTING3D_INSTANTNGP_ROOT:-${REPAINTING3D_INSTANTNGP_ROOT_DEFAULT}}"

REPAINTING3D_BUILD_INSTALL_ROOT_DEFAULT="${REPAINTING3D_ROOT}/tools"
REPAINTING3D_BUILD_INSTALL_ROOT="${REPAINTING3D_BUILD_INSTALL_ROOT:-${REPAINTING3D_BUILD_INSTALL_ROOT_DEFAULT}}"

REPAINTING3D_OUT_SHAPENET_DEFAULT="${REPAINTING3D_ROOT}/out_shapenet"
REPAINTING3D_OUT_SHAPENET="${REPAINTING3D_OUT_SHAPENET:-${REPAINTING3D_OUT_SHAPENET_DEFAULT}}"
mkdir -p "${REPAINTING3D_OUT_SHAPENET}"

SELF="$(readlink -f "$0")"
SELF_DIR="$(dirname "${SELF}")"
REPAINTING3D_CODE_ROOT="$(readlink -f "${SELF_DIR}/..")"

export TRANSFORMERS_CACHE="${REPAINTING3D_ROOT}/hfcache"
export HF_DATASETS_CACHE="${REPAINTING3D_ROOT}/hfcache"
export HF_HOME="${REPAINTING3D_ROOT}/hfcache"

cd "${REPAINTING3D_CODE_ROOT}" && python -m repainting_3d_assets.main_shapenet \
    --path_instantngp "${REPAINTING3D_INSTANTNGP_ROOT}" \
    --path_shapenet "${REPAINTING3D_DATASET_ROOT}" \
    --path_out "${REPAINTING3D_OUT_SHAPENET}" \
    --range_ids_list "$@"
