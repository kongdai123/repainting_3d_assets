#!/usr/bin/env bash
set -e
set -x

if [ $# -ne 4 ]; then
    echo "Error: Insufficient command line arguments:"
    echo "$0 <working_dir> <path_input> <path_output> <prompt>"
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

SL3A_ROOT="$1"
shift
PATH_IN=$(realpath "$1")
shift
PATH_OUT=$(realpath "$1")
shift
PROMPT="$1"
shift

SL3A_CONDA_ROOT="${SL3A_ROOT}/conda"
if [ ! -f "${SL3A_CONDA_ROOT}/miniconda3/bin/conda" ]; then
    echo "\"conda\" not found, check setup_conda_bin.sh"
    exit 255
fi
source "${SL3A_CONDA_ROOT}/miniconda3/bin/activate" ${SL3A_ENV_NAME}

SL3A_INSTANTNGP_ROOT_DEFAULT="${SL3A_ROOT}/instantngp"
SL3A_INSTANTNGP_ROOT="${SL3A_INSTANTNGP_ROOT:-${SL3A_INSTANTNGP_ROOT_DEFAULT}}"

mkdir -p "${PATH_OUT}"

SELF=$(realpath "$0")
SELF_DIR=$(dirname "${SELF}")
SL3A_CODE_ROOT=$(realpath "${SELF_DIR}/..")

export TRANSFORMERS_CACHE="${SL3A_ROOT}/hfcache"
export HF_DATASETS_CACHE="${SL3A_ROOT}/hfcache"
export HF_HOME="${SL3A_ROOT}/hfcache"

cd "${SL3A_CODE_ROOT}" && python -m sl3a.main_one \
    --path_instantngp "${SL3A_INSTANTNGP_ROOT}/instant-ngp" \
    --path_in "${PATH_IN}" \
    --path_out "${PATH_OUT}" \
    --prompt "${PROMPT}" \
    "$@"
