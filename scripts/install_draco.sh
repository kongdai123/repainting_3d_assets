#!/usr/bin/env bash
set -e
if ! type source > /dev/null 2>&1; then
    bash "$0" "$@"
    exit $?
fi
if [ ! -z "${DEBUG}" ]; then
    set -x
fi

PREFIX=""
if [ $# -ge 1 ]; then
    PREFIX="$(readlink -f "$1")"
fi

if type draco_encoder > /dev/null 2>&1 || [ -f "${PREFIX}/bin/draco_encoder" ]; then
    echo "DRACO already installed"
    exit 0
fi

DRACO_VERSION=1.5.6

CMAKE_EXTRA_ARGS=""
if [ ! -z "${PREFIX}" ]; then
    CMAKE_EXTRA_ARGS+=" -DCMAKE_INSTALL_RPATH_USE_LINK_PATH=TRUE"
    CMAKE_EXTRA_ARGS+=" -DCMAKE_PREFIX_PATH="${PREFIX}""
    CMAKE_EXTRA_ARGS+=" -DCMAKE_INSTALL_PREFIX="${PREFIX}""
fi

git clone https://github.com/google/draco.git
cd draco
git checkout v156_snapshot
git submodule update --init
cmake \
    -B build \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH="${REPAINTING3D_INSTALL_PREFIX}" \
    -DCMAKE_INSTALL_PREFIX="${REPAINTING3D_INSTALL_PREFIX}" \
    -DDRACO_TRANSCODER_SUPPORTED=ON \
     ${CMAKE_EXTRA_ARGS}
cmake --build build --target install -j

if [ ! -z "${CLEANUP}" ]; then
    cd ..
    rm -rf draco
fi
