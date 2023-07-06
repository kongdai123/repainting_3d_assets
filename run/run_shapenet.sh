#!/usr/bin/env bash
set -e
set -x

SL3A_ENV_NAME=${SL3A_ENV_NAME:-sl3a}

if [ $# -lt 2 ]; then
    echo "Error: Insufficient command line arguments:"
    echo "$0 <working_dir> [list_of_shapenet_model_ids]"
    exit 255
fi

SL3A_ROOT=$1
shift

SL3A_CONDA_ROOT="${SL3A_ROOT}/conda"
SL3A_DATASET_ROOT="${SL3A_ROOT}/dataset"
export SL3A_INSTANTNGP_ROOT="${SL3A_ROOT}/instantngp"  # TODO: make sure the code does not use any of the SL3A env vars

if [ ! -f "${SL3A_CONDA_ROOT}/miniconda3/bin/conda" ]; then
    echo "\"conda\" not found, check setup_conda_bin.sh"
    exit 255
fi

source "${SL3A_CONDA_ROOT}/miniconda3/bin/activate" ${SL3A_ENV_NAME}

SELF=$(realpath "$0")
SELF_DIR=$(dirname "${SELF}")
SL3A_CODE_ROOT=$(realpath "${SELF_DIR}/..")

SL3A_OUT_SHAPENET="${SL3A_ROOT}/out_shapenet"
mkdir -p "${SL3A_OUT_SHAPENET}"

cd "${SL3A_CODE_ROOT}" && python -m main \
    --path_shapenet "${SL3A_DATASET_ROOT}" \
    --path_out "${SL3A_OUT_SHAPENET}" \
    --range_ids_list "$@"
