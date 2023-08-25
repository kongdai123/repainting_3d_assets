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
REPAINTING3D_CODE_ROOT=$(realpath "${SELF_DIR}/..")

if [ -z "${REPAINTING3D_CONDA_ROOT}" ]; then
    echo "REPAINTING3D_CONDA_ROOT not set or is empty"
    exit 255
fi

if [ -z "${REPAINTING3D_BUILD_INSTALL_ROOT}" ]; then
    echo "REPAINTING3D_BUILD_INSTALL_ROOT not set or is empty"
    exit 255
fi

if [ ! -f "${REPAINTING3D_CONDA_ROOT}/miniconda3/bin/conda" ]; then
    echo "\"conda\" not found, check setup_conda_bin.sh"
    exit 255
fi

REPAINTING3D_ENV_NAME="${REPAINTING3D_ENV_NAME:-repainting_3d_assets}"

REMESH_VERSION=56413d10

source "${REPAINTING3D_CONDA_ROOT}/miniconda3/bin/activate" "${REPAINTING3D_ENV_NAME}"

REPAINTING3D_INSTALL_PREFIX="${REPAINTING3D_BUILD_INSTALL_ROOT}/prefix"
mkdir -p "${REPAINTING3D_INSTALL_PREFIX}"

if [ ! -f "${REPAINTING3D_INSTALL_PREFIX}/.marker.dep6.remesher.installed" ]; then
    cd "${REPAINTING3D_BUILD_INSTALL_ROOT}"
    rm -rf remesh_isotropic_planar
    git clone https://github.com/toshas/remesh_isotropic_planar.git
    cd remesh_isotropic_planar
    git checkout ${REMESH_VERSION}
    cmake -B build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_RPATH_USE_LINK_PATH=TRUE \
        -DCMAKE_PREFIX_PATH="${REPAINTING3D_CONDA_ROOT}/miniconda3/envs/${REPAINTING3D_ENV_NAME}" \
        -DCMAKE_INSTALL_PREFIX="${REPAINTING3D_CONDA_ROOT}/miniconda3/envs/${REPAINTING3D_ENV_NAME}"
    cmake --build build --target install -j
    touch "${REPAINTING3D_INSTALL_PREFIX}/.marker.dep6.remesher.installed"
fi
