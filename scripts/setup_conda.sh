#!/usr/bin/env bash
set -e
if [ ! -z "${DEBUG}" ]; then
    set -x
fi

if ! type source > /dev/null 2>&1; then
    if [ ! -z "${DEBUG}" ]; then
        echo "Restarting the script with bash interpreter"
    fi
    bash "$0" "$@"
    exit $?
fi
SELF=$(readlink -f "${BASH_SOURCE[0]}")
SELF_DIR=$(dirname "${SELF}")

if [ -n "$CONDA_PREFIX" ]; then
    echo "Deactivating Conda environment: $CONDA_PREFIX"
    conda deactivate
fi

if [ -z "${REPAINTING3D_CONDA_ROOT}" ]; then
    echo "REPAINTING3D_CONDA_ROOT not set or is empty"
    exit 255
fi

if [ -f "${REPAINTING3D_CONDA_ROOT}/.marker.conda.completed" ]; then
    echo "Conda already installed"
    exit 0
fi

REPAINTING3D_CONDA_INSTALLER_FILE="${REPAINTING3D_CONDA_INSTALLER_FILE:-Miniconda3-py38_23.3.1-0-Linux-x86_64.sh}"
REPAINTING3D_ENV_NAME="${REPAINTING3D_ENV_NAME:-repainting_3d_assets}"

rm -rf "${REPAINTING3D_CONDA_ROOT}"
mkdir -p "${REPAINTING3D_CONDA_ROOT}"
cd "${REPAINTING3D_CONDA_ROOT}"

wget https://repo.anaconda.com/miniconda/${REPAINTING3D_CONDA_INSTALLER_FILE}
bash ${REPAINTING3D_CONDA_INSTALLER_FILE} -b -p "${REPAINTING3D_CONDA_ROOT}/miniconda3"

CONDA="${REPAINTING3D_CONDA_ROOT}/miniconda3/bin/conda"
CONDA_ACTIVATE="${REPAINTING3D_CONDA_ROOT}/miniconda3/bin/activate"

if [ ! -f "${CONDA}" -o ! -f "${CONDA_ACTIVATE}" ]; then
    echo "\"conda\" not found"
    exit 255
fi

"${CONDA}" install -q -y -n base --solver classic conda-libmamba-solver
"${CONDA}" config --set solver libmamba

"${CONDA}" env create -q -y -n ${REPAINTING3D_ENV_NAME} -f "${SELF_DIR}/environment.yml"

touch "${REPAINTING3D_CONDA_ROOT}/.marker.conda.completed"
