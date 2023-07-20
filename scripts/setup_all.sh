#!/usr/bin/env bash
set -e
set -x

if [ $# -ne 1 ]; then
    echo "Error: Exactly one argument is required - path to the working directory"
    exit 255
fi

SELF=$(realpath "$0")
SELF_DIR=$(dirname "${SELF}")

export SL3A_ROOT=$1

export SL3A_CONDA_ROOT="${SL3A_ROOT}/conda"
export SL3A_DATASET_ROOT="${SL3A_ROOT}/dataset"
export SL3A_INSTANTNGP_ROOT="${SL3A_ROOT}/instantngp"

export TRANSFORMERS_CACHE="${SL3A_ROOT}/hfcache"
export HF_DATASETS_CACHE="${SL3A_ROOT}/hfcache"
export HF_HOME="${SL3A_ROOT}/hfcache"

bash "${SELF_DIR}/setup_conda_bin.sh"
bash "${SELF_DIR}/setup_conda_env.sh"
bash "${SELF_DIR}/setup_instantngp.sh"

bash "${SELF_DIR}/setup_dataset_shapenet.sh"
