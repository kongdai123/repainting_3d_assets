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

if type remesh_isotropic_planar > /dev/null 2>&1 || [ -f "${PREFIX}/bin/remesh_isotropic_planar" ]; then
    echo "Model export already installed"
    exit 0
fi

REMESH_VERSION=56413d10

CMAKE_EXTRA_ARGS=""
if [ ! -z "${PREFIX}" ]; then
    CMAKE_EXTRA_ARGS+=" -DCMAKE_INSTALL_RPATH_USE_LINK_PATH=TRUE"
    CMAKE_EXTRA_ARGS+=" -DCMAKE_PREFIX_PATH="${PREFIX}""
    CMAKE_EXTRA_ARGS+=" -DCMAKE_INSTALL_PREFIX="${PREFIX}""
fi

rm -rf remesh_isotropic_planar
git clone https://github.com/toshas/remesh_isotropic_planar.git
cd remesh_isotropic_planar
git checkout ${REMESH_VERSION}
cmake -B build -DCMAKE_BUILD_TYPE=Release ${CMAKE_EXTRA_ARGS}
cmake --build build --target install -j

if [ ! -z "${CLEANUP}" ]; then
    cd ..
    rm -rf remesh_isotropic_planar
fi
