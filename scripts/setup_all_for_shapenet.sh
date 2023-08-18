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

export SL3A_ROOT=$1

export SL3A_CONDA_ROOT="${SL3A_ROOT}/conda"
export SL3A_DATASET_ROOT="${SL3A_ROOT}/dataset"
export SL3A_INSTANTNGP_ROOT="${SL3A_ROOT}/instantngp"
export SL3A_BUILD_INSTALL_ROOT="${SL3A_ROOT}/tools"

export TRANSFORMERS_CACHE="${SL3A_ROOT}/hfcache"
export HF_DATASETS_CACHE="${SL3A_ROOT}/hfcache"
export HF_HOME="${SL3A_ROOT}/hfcache"

bash "${SELF_DIR}/setup_conda.sh"
bash "${SELF_DIR}/setup_instantngp.sh"
bash "${SELF_DIR}/setup_model_export.sh"

if [ -z "${DISABLE_SHAPENET}" ]; then
    bash "${SELF_DIR}/setup_dataset_shapenet.sh"
fi
