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
SL3A_CODE_ROOT=$(realpath "${SELF_DIR}/..")

if [ -z "${SL3A_CONDA_ROOT}" ]; then
    echo "SL3A_CONDA_ROOT not set or is empty"
    exit 255
fi

if [ -z "${SL3A_INSTANTNGP_ROOT}" ]; then
    echo "SL3A_INSTANTNGP_ROOT not set or is empty"
    exit 255
fi

if [ ! -f "${SL3A_CONDA_ROOT}/miniconda3/bin/conda" ]; then
    echo "\"conda\" not found, check setup_conda_bin.sh"
    exit 255
fi

SL3A_ENV_NAME="${SL3A_ENV_NAME:-sl3a}"

source "${SL3A_CONDA_ROOT}/miniconda3/bin/activate" "${SL3A_ENV_NAME}"

mkdir -p "${SL3A_INSTANTNGP_ROOT}"
cd "${SL3A_INSTANTNGP_ROOT}"
if [ ! -f "${SL3A_INSTANTNGP_ROOT}/.marker.ingp.cloned" ]; then
    git clone https://github.com/nvlabs/instant-ngp
    cd instant-ngp
    git reset --hard 54aba7cfbeaf6a60f29469a9938485bebeba24c3
    git submodule update --init --recursive
    find . -type d -name .git -exec rm -rf {} +
    touch "${SL3A_INSTANTNGP_ROOT}/.marker.ingp.cloned"
else
    cd instant-ngp
fi

if [ ! -f "${SL3A_INSTANTNGP_ROOT}/.marker.ingp.patched" ]; then
    cd dependencies/tiny-cuda-nn/include/tiny-cuda-nn/encodings/
    patch -N -p1 -i "${SL3A_CODE_ROOT}/sl3a/nerf_reconstruction/instant_ngp_patches/00_grid_h.patch"
    cd "${SL3A_INSTANTNGP_ROOT}/instant-ngp"
    cp "${SL3A_CODE_ROOT}/sl3a/nerf_reconstruction/instant_ngp_patches/fine_network.json" "${SL3A_INSTANTNGP_ROOT}/instant-ngp/configs/nerf/"
    touch "${SL3A_INSTANTNGP_ROOT}/.marker.ingp.patched"
fi

SL3A_INSTANTNGP_ARCHS=${SL3A_INSTANTNGP_ARCHS:-"60 70 75 80 86 89 90"}

for ARCH in ${SL3A_INSTANTNGP_ARCHS}; do
    if [ -f "${SL3A_INSTANTNGP_ROOT}/.marker.ingp.compiled.sm${ARCH}" ]; then
        continue
    fi
    echo "Compiling InstantNGP for architecture $ARCH"
    cmake . -B build_sm${ARCH} -DNGP_BUILD_WITH_GUI=OFF -DTCNN_CUDA_ARCHITECTURES=${ARCH}
    cmake --build build_sm${ARCH} --config RelWithDebInfo -j 4
    touch "${SL3A_INSTANTNGP_ROOT}/.marker.ingp.compiled.sm${ARCH}"
done
