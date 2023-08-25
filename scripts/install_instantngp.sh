#!/usr/bin/env bash
set -e
if [ ! -z "${DEBUG}" ]; then
    set -x
fi

if [ $# -ne 3 ]; then
    echo "Error: Expecting three arguments: <installation path> <patches path> <space delimited architectures>"
    exit 255
fi
NGP_ROOT="$(readlink -f "$1")"
NGP_PATCHES="$(readlink -f "$2")"
NGP_ARCHS="$3"

mkdir -p "${NGP_ROOT}"
cd "${NGP_ROOT}"
if [ ! -f "${NGP_ROOT}/.marker.ingp.cloned" ]; then
    git clone https://github.com/nvlabs/instant-ngp
    cd instant-ngp
    git reset --hard 54aba7cfbeaf6a60f29469a9938485bebeba24c3
    git submodule update --init --recursive
    find . -type d -name .git -exec rm -rf {} +
    touch "${NGP_ROOT}/.marker.ingp.cloned"
else
    cd instant-ngp
fi

if [ ! -f "${NGP_ROOT}/.marker.ingp.patched" ]; then
    patch -N -p1 -i "${NGP_PATCHES}/00_finer_nerf_hash_grid.patch"
    patch -N -p1 -i "${NGP_PATCHES}/01_mesh_guided_nerf_sampling.patch"
    touch "${NGP_ROOT}/.marker.ingp.patched"
fi

for ARCH in ${NGP_ARCHS}; do
    if [ -f "${NGP_ROOT}/.marker.ingp.compiled.sm${ARCH}" ]; then
        continue
    fi
    echo "Compiling InstantNGP for architecture $ARCH"
    cmake . -B build_sm${ARCH} -DNGP_BUILD_WITH_GUI=OFF -DTCNN_CUDA_ARCHITECTURES=${ARCH}
    cmake --build build_sm${ARCH} --config RelWithDebInfo -j 4
    touch "${NGP_ROOT}/.marker.ingp.compiled.sm${ARCH}"
done
