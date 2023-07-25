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

if [ -n "$CONDA_PREFIX" ]; then
    echo "Deactivating Conda environment: $CONDA_PREFIX"
    conda deactivate
fi

if [ -z "${SL3A_CONDA_ROOT}" ]; then
    echo "SL3A_CONDA_ROOT not set or is empty"
    exit 255
fi

SL3A_ENV_NAME="${SL3A_ENV_NAME:-sl3a}"
SL3A_ENV_NAME_TMP=tmp

CONDA="${SL3A_CONDA_ROOT}/miniconda3/bin/conda"
CONDA_ACTIVATE="${SL3A_CONDA_ROOT}/miniconda3/bin/activate"

if [ ! -z "${SL3A_CONDA_PERFORM_SETUP}" ]; then
    if [ ! -f "${CONDA}" ]; then
        echo "\"conda\" not found, check setup_conda_bin.sh"
        exit 255
    fi

    if "${CONDA}" env list | grep -qw "^${SL3A_ENV_NAME}"; then
        echo "Conda environment \"${SL3A_ENV_NAME}\" already exists"
        exit 0
    fi

    "${CONDA}" create -y -n ${SL3A_ENV_NAME_TMP} python=3.9

    source "${CONDA_ACTIVATE}" ${SL3A_ENV_NAME_TMP}

    "${CONDA}" install -y pytorch=1.13.0 torchvision=0.14.0 pytorch-cuda=11.6 numpy==1.21.2 -c pytorch -c nvidia
    "${CONDA}" install -y -c fvcore -c iopath -c conda-forge fvcore=0.1.5.post20221221 iopath=0.1.9 ffmpeg=4.3
    "${CONDA}" install -y pytorch3d=0.7.4 -c pytorch3d

    pip install -r "${SELF_DIR}/requirements.txt"

    exit 0
fi

if [ ! -z "${SL3A_CONDA_FINALIZE_SETUP}" ]; then
    if "${CONDA}" env list | grep -qw "^${SL3A_ENV_NAME}"; then
        exit 0
    fi

    "${CONDA}" rename -n "${SL3A_ENV_NAME_TMP}" "${SL3A_ENV_NAME}"

    exit 0
fi

# 1. conda renaming is required to ensure consistency of the new environment with respect to the many steps involved in its setup
# 2. conda renaming cannot be done from within the activated environment, and deactivation is unavailable in unattended mode, so
#    we just split installation into two executions of this very script activating two different code paths.
SL3A_CONDA_PERFORM_SETUP=1 bash "$0" "$@"
SL3A_CONDA_FINALIZE_SETUP=1 bash "$0" "$@"

echo "Conda environment \"${SL3A_ENV_NAME}\" is now installed"
