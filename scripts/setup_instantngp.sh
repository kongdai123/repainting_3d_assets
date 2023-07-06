#!/usr/bin/env bash
set -e
set -x

if [ -z "${SL3A_INSTANTNGP_ROOT}" ]; then
    echo "SL3A_INSTANTNGP_ROOT not set or is empty"
    exit 255
fi

if ! type shopt > /dev/null 2>&1; then
    echo "This script requires bash interpreter"
    exit 255
fi

SELF=$(realpath "$0")
SELF_DIR=$(dirname "${SELF}")
SL3A_CODE_ROOT=$(realpath "${SELF_DIR}/..")

SL3A_ENV_NAME=${SL3A_ENV_NAME:-sl3a}

if [ ! -f "${SL3A_CONDA_ROOT}/miniconda3/bin/conda" ]; then
    echo "\"conda\" not found, check setup_conda_bin.sh"
    exit 255
fi

# conda activate ${SL3A_ENV_NAME}
source "${SL3A_CONDA_ROOT}/miniconda3/bin/activate" ${SL3A_ENV_NAME}

mkdir -p "${SL3A_INSTANTNGP_ROOT}"
cd "${SL3A_INSTANTNGP_ROOT}"
if [ ! -f "${SL3A_ROOT}/.marker.ingp.cloned" ]; then
    git clone https://github.com/nvlabs/instant-ngp
    cd instant-ngp
    git reset --hard 54aba7cfbeaf6a60f29469a9938485bebeba24c3
    git submodule update --init --recursive
    touch "${SL3A_ROOT}/.marker.ingp.cloned"
else
    cd instant-ngp
fi

if [ ! -f "${SL3A_ROOT}/.marker.ingp.patched" ]; then
    cp "${SL3A_CODE_ROOT}/nerf_recon/ngp_files/grid.h" dependencies/tiny-cuda-nn/include/tiny-cuda-nn/encodings/
    cp "${SL3A_CODE_ROOT}/nerf_recon/ngp_files/fine_network.json" configs/nerf/
    touch "${SL3A_ROOT}/.marker.ingp.patched"
fi

if [ ! -f "${SL3A_ROOT}/.marker.ingp.compiled.sm75" ]; then
    cmake . -B build_sm75 -DNGP_BUILD_WITH_GUI=OFF -DTCNN_CUDA_ARCHITECTURES=75
    cmake --build build_sm75 --config RelWithDebInfo -j 4
    touch "${SL3A_ROOT}/.marker.ingp.compiled.sm75"
fi

if [ ! -f "${SL3A_ROOT}/.marker.ingp.compiled.sm86" ]; then
    cmake . -B build_sm86 -DNGP_BUILD_WITH_GUI=OFF -DTCNN_CUDA_ARCHITECTURES=86
    cmake --build build_sm86 --config RelWithDebInfo -j 4
    touch "${SL3A_ROOT}/.marker.ingp.compiled.sm86"
fi
