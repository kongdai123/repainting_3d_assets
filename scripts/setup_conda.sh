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

if [ -f "${SL3A_CONDA_ROOT}/.marker.conda.completed" ]; then
    echo "Conda already installed"
    exit 0
fi

SL3A_CONDA_INSTALLER_FILE="${SL3A_CONDA_INSTALLER_FILE:-Miniconda3-py38_23.3.1-0-Linux-x86_64.sh}"
SL3A_ENV_NAME="${SL3A_ENV_NAME:-sl3a}"

rm -rf "${SL3A_CONDA_ROOT}"
mkdir -p "${SL3A_CONDA_ROOT}"
cd "${SL3A_CONDA_ROOT}"

wget https://repo.anaconda.com/miniconda/${SL3A_CONDA_INSTALLER_FILE}
bash ${SL3A_CONDA_INSTALLER_FILE} -b -p "${SL3A_CONDA_ROOT}/miniconda3"

CONDA="${SL3A_CONDA_ROOT}/miniconda3/bin/conda"
CONDA_ACTIVATE="${SL3A_CONDA_ROOT}/miniconda3/bin/activate"

if [ ! -f "${CONDA}" -o ! -f "${CONDA_ACTIVATE}" ]; then
    echo "\"conda\" not found"
    exit 255
fi

"${CONDA}" install -y -n base --solver classic conda-libmamba-solver
"${CONDA}" config --set solver libmamba

"${CONDA}" env create -y -n ${SL3A_ENV_NAME} -f "${SELF_DIR}/environment.yml"

touch "${SL3A_CONDA_ROOT}/.marker.conda.completed"
