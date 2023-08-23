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

if [ -z "${REPAINTING3D_INSTANTNGP_ROOT}" ]; then
    echo "REPAINTING3D_INSTANTNGP_ROOT not set or is empty"
    exit 255
fi

if [ ! -f "${REPAINTING3D_CONDA_ROOT}/miniconda3/bin/conda" ]; then
    echo "\"conda\" not found, check setup_conda_bin.sh"
    exit 255
fi

REPAINTING3D_ENV_NAME="${REPAINTING3D_ENV_NAME:-repainting_3d_assets}"

source "${REPAINTING3D_CONDA_ROOT}/miniconda3/bin/activate" "${REPAINTING3D_ENV_NAME}"

mkdir -p "${REPAINTING3D_INSTANTNGP_ROOT}"
cd "${REPAINTING3D_INSTANTNGP_ROOT}"
if [ ! -f "${REPAINTING3D_INSTANTNGP_ROOT}/.marker.ingp.cloned" ]; then
    git clone https://github.com/nvlabs/instant-ngp
    cd instant-ngp
    git reset --hard 54aba7cfbeaf6a60f29469a9938485bebeba24c3
    git submodule update --init --recursive
    find . -type d -name .git -exec rm -rf {} +
    touch "${REPAINTING3D_INSTANTNGP_ROOT}/.marker.ingp.cloned"
else
    cd instant-ngp
fi

if [ ! -f "${REPAINTING3D_INSTANTNGP_ROOT}/.marker.ingp.patched" ]; then
    patch -N -p1 -i "${REPAINTING3D_CODE_ROOT}/repainting_3d_assets/nerf_reconstruction/instant_ngp_patches/00_finer_nerf_hash_grid.patch"
    patch -N -p1 -i "${REPAINTING3D_CODE_ROOT}/repainting_3d_assets/nerf_reconstruction/instant_ngp_patches/01_mesh_guided_nerf_sampling.patch"
    touch "${REPAINTING3D_INSTANTNGP_ROOT}/.marker.ingp.patched"
fi

REPAINTING3D_INSTANTNGP_ARCHS=${REPAINTING3D_INSTANTNGP_ARCHS:-"60 70 75 80 86 89 90"}

for ARCH in ${REPAINTING3D_INSTANTNGP_ARCHS}; do
    if [ -f "${REPAINTING3D_INSTANTNGP_ROOT}/.marker.ingp.compiled.sm${ARCH}" ]; then
        continue
    fi
    echo "Compiling InstantNGP for architecture $ARCH"
    cmake . -B build_sm${ARCH} -DNGP_BUILD_WITH_GUI=OFF -DTCNN_CUDA_ARCHITECTURES=${ARCH}
    cmake --build build_sm${ARCH} --config RelWithDebInfo -j 4
    touch "${REPAINTING3D_INSTANTNGP_ROOT}/.marker.ingp.compiled.sm${ARCH}"
done
