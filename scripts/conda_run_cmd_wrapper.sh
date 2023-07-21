#!/usr/bin/env bash
set -e
set -x

if [ $# -lt 2 ]; then
    echo "Error: Insufficient command line arguments:"
    echo "$0 <working_dir> [wrapped command to run]"
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

"$@"
