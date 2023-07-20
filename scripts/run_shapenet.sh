#!/usr/bin/env bash
set -e
set -x

if [ $# -lt 2 ]; then
    echo "Error: Insufficient command line arguments:"
    echo "$0 <working_dir> [list_of_shapenet_model_ids]"
    exit 255
fi

if ! type source > /dev/null 2>&1; then
    echo "Restarting the script with bash interpreter"
    bash "$0" "$@"
    exit $?
fi

if [ -n "$CONDA_PREFIX" ]; then
    echo "Deactivating Conda environment: $CONDA_PREFIX"
    conda deactivate
fi

SL3A_ENV_NAME=${SL3A_ENV_NAME:-sl3a}

SL3A_ROOT=$1
shift

SL3A_CONDA_ROOT="${SL3A_ROOT}/conda"
if [ ! -f "${SL3A_CONDA_ROOT}/miniconda3/bin/conda" ]; then
    echo "\"conda\" not found, check setup_conda_bin.sh"
    exit 255
fi
source "${SL3A_CONDA_ROOT}/miniconda3/bin/activate" ${SL3A_ENV_NAME}

SL3A_DATASET_ROOT_DEFAULT="${SL3A_ROOT}/dataset"
SL3A_DATASET_ROOT="${SL3A_DATASET_ROOT:-${SL3A_DATASET_ROOT_DEFAULT}}"

SL3A_INSTANTNGP_ROOT_DEFAULT="${SL3A_ROOT}/instantngp"
SL3A_INSTANTNGP_ROOT="${SL3A_INSTANTNGP_ROOT:-${SL3A_INSTANTNGP_ROOT_DEFAULT}}"

SL3A_OUT_SHAPENET_DEFAULT="${SL3A_ROOT}/out_shapenet"
SL3A_OUT_SHAPENET="${SL3A_OUT_SHAPENET:-${SL3A_OUT_SHAPENET_DEFAULT}}"
mkdir -p "${SL3A_OUT_SHAPENET}"

SELF=$(realpath "$0")
SELF_DIR=$(dirname "${SELF}")
SL3A_CODE_ROOT=$(realpath "${SELF_DIR}/..")

export TRANSFORMERS_CACHE="${SL3A_ROOT}/hfcache"
export HF_DATASETS_CACHE="${SL3A_ROOT}/hfcache"
export HF_HOME="${SL3A_ROOT}/hfcache"

cd "${SL3A_CODE_ROOT}" && python -m main \
    --path_instantngp "${SL3A_INSTANTNGP_ROOT}/instant-ngp" \
    --path_shapenet "${SL3A_DATASET_ROOT}" \
    --path_out "${SL3A_OUT_SHAPENET}" \
    --range_ids_list "$@"
