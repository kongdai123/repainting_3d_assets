#!/usr/bin/env bash
set -e
if [ ! -z "${DEBUG}" ]; then
    set -x
fi

if [ $# -ne 2 ]; then
    echo "Error: Expecting one argument: <env installation path> <env spec path>"
    exit 255
fi
ENV_ROOT="$1"
ENV_SPEC="$(readlink -f "$2")"

if [ -n "$CONDA_PREFIX" ]; then
    conda deactivate
fi

if [ -f "${ENV_ROOT}/.marker.conda.completed" ]; then
    echo "Environment already installed"
    exit 0
fi

INSTALLER=Miniconda3-py38_23.3.1-0-Linux-x86_64.sh
REPAINTING3D_ENV_NAME=${REPAINTING3D_ENV_NAME:-repainting_3d_assets}

rm -rf "${ENV_ROOT}"
mkdir -p "${ENV_ROOT}"
cd "${ENV_ROOT}"

wget https://repo.anaconda.com/miniconda/${INSTALLER}
bash ${INSTALLER} -b -p "${ENV_ROOT}/miniconda3"

CONDA="${ENV_ROOT}/miniconda3/bin/conda"
CONDA_ACTIVATE="${ENV_ROOT}/miniconda3/bin/activate"

"${CONDA}" install -q -y -n base --solver classic conda-libmamba-solver
"${CONDA}" env create -q -y -n "${REPAINTING3D_ENV_NAME}" -f "${ENV_SPEC}" --solver libmamba

touch "${ENV_ROOT}/.marker.conda.completed"
