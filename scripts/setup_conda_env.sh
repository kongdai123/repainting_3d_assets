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

if [ -f "${SL3A_CONDA_ROOT}/.marker.env.completed" ]; then
    echo "Environment already installed"
    exit 0
fi

SL3A_ENV_NAME="${SL3A_ENV_NAME:-sl3a}"

CONDA="${SL3A_CONDA_ROOT}/miniconda3/bin/conda"
CONDA_ACTIVATE="${SL3A_CONDA_ROOT}/miniconda3/bin/activate"

if [ ! -f "${CONDA}" -o ! -f "${CONDA_ACTIVATE}" ]; then
    echo "\"conda\" not found, check setup_conda_bin.sh"
    exit 255
fi

if "${CONDA}" env list | grep -qw "^${SL3A_ENV_NAME}"; then
    "${CONDA}" env remove -n ${SL3A_ENV_NAME}
fi

"${CONDA}" install -y -n base --solver classic conda-libmamba-solver
"${CONDA}" config --set solver libmamba

"${CONDA}" create -y -n ${SL3A_ENV_NAME} python=3.9

source "${CONDA_ACTIVATE}" ${SL3A_ENV_NAME}

"${CONDA}" install -y pytorch=1.13.0 pytorch-cuda=11.6 numpy==1.21.2 -c pytorch -c nvidia
"${CONDA}" install -y -c fvcore -c iopath -c conda-forge fvcore=0.1.5.post20221221 iopath=0.1.9 ffmpeg=4.3 cmake=3.26.4
"${CONDA}" install -y pytorch3d=0.7.4 -c pytorch3d
pip install -r "${SELF_DIR}/requirements.txt"

touch "${SL3A_CONDA_ROOT}/.marker.env.completed"
echo "Conda environment \"${SL3A_ENV_NAME}\" is now installed"
