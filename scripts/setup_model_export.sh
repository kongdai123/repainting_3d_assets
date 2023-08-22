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

BOOST_VERSION=1.82.0
GMP_VERSION=6.2.1
MPFR_VERSION=4.2.0
EIGEN_VERSION=3.4.0
CGAL_VERSION=5.6-beta1
REMESH_VERSION=56413d10
DRACO_VERSION=1.5.6

source "${REPAINTING3D_CONDA_ROOT}/miniconda3/bin/activate" "${REPAINTING3D_ENV_NAME}"

REPAINTING3D_INSTALL_PREFIX="${REPAINTING3D_BUILD_INSTALL_ROOT}/prefix"
mkdir -p "${REPAINTING3D_INSTALL_PREFIX}"

if [ ! -f "${REPAINTING3D_INSTALL_PREFIX}/.marker.dep1.boost.installed" ]; then
    BOOST_VERSION_UNDERSCORE=${BOOST_VERSION//./_}
    cd "${REPAINTING3D_BUILD_INSTALL_ROOT}"
    wget https://boostorg.jfrog.io/artifactory/main/release/${BOOST_VERSION}/source/boost_${BOOST_VERSION_UNDERSCORE}.tar.gz
    tar -xf boost_${BOOST_VERSION_UNDERSCORE}.tar.gz
    cd boost_${BOOST_VERSION_UNDERSCORE}
    ./bootstrap.sh --prefix="${REPAINTING3D_INSTALL_PREFIX}"
    ./b2 install -j4
    touch "${REPAINTING3D_INSTALL_PREFIX}/.marker.dep1.boost.installed"
fi

if [ ! -f "${REPAINTING3D_INSTALL_PREFIX}/.marker.dep2.gmp.installed" ]; then
    cd "${REPAINTING3D_BUILD_INSTALL_ROOT}"
    wget https://gmplib.org/download/gmp/gmp-${GMP_VERSION}.tar.xz
    tar -xf gmp-${GMP_VERSION}.tar.xz
    cd gmp-${GMP_VERSION}
    ./configure --prefix="${REPAINTING3D_INSTALL_PREFIX}"
    make
    make check
    make install
    touch "${REPAINTING3D_INSTALL_PREFIX}/.marker.dep2.gmp.installed"
fi

if [ ! -f "${REPAINTING3D_INSTALL_PREFIX}/.marker.dep3.mpfr.installed" ]; then
    cd "${REPAINTING3D_BUILD_INSTALL_ROOT}"
    wget https://www.mpfr.org/mpfr-${MPFR_VERSION}/mpfr-${MPFR_VERSION}.tar.xz
    tar -xf mpfr-${MPFR_VERSION}.tar.xz
    cd mpfr-${MPFR_VERSION}
    ./configure --prefix="${REPAINTING3D_INSTALL_PREFIX}" --with-gmp="${REPAINTING3D_INSTALL_PREFIX}"
    make
    make check
    make install
    touch "${REPAINTING3D_INSTALL_PREFIX}/.marker.dep3.mpfr.installed"
fi

if [ ! -f "${REPAINTING3D_INSTALL_PREFIX}/.marker.dep4.eigen.installed" ]; then
    cd "${REPAINTING3D_BUILD_INSTALL_ROOT}"
    wget https://gitlab.com/libeigen/eigen/-/archive/3.4.0/eigen-${EIGEN_VERSION}.tar.gz
    tar -xf eigen-${EIGEN_VERSION}.tar.gz
    cd eigen-${EIGEN_VERSION}
    mkdir -p build
    cd build
    cmake \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_PREFIX_PATH="${REPAINTING3D_INSTALL_PREFIX}" \
        -DCMAKE_INSTALL_PREFIX="${REPAINTING3D_INSTALL_PREFIX}" \
        ..
    make install
    touch "${REPAINTING3D_INSTALL_PREFIX}/.marker.dep4.eigen.installed"
fi

if [ ! -f "${REPAINTING3D_INSTALL_PREFIX}/.marker.dep5.cgal.installed" ]; then
    cd "${REPAINTING3D_BUILD_INSTALL_ROOT}"
    wget https://github.com/CGAL/cgal/releases/download/v5.6-beta1/CGAL-${CGAL_VERSION}-library.tar.xz
    tar -xf CGAL-${CGAL_VERSION}-library.tar.xz
    cd CGAL-${CGAL_VERSION}
    mkdir -p build
    cd build
    cmake \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_PREFIX_PATH="${REPAINTING3D_INSTALL_PREFIX}" \
        -DCMAKE_INSTALL_PREFIX="${REPAINTING3D_INSTALL_PREFIX}" \
        -DWITH_CGAL_Qt5=OFF \
        ..
    make install
    touch "${REPAINTING3D_INSTALL_PREFIX}/.marker.dep5.cgal.installed"
fi

if [ ! -f "${REPAINTING3D_INSTALL_PREFIX}/.marker.dep6.remesher.installed" ]; then
    cd "${REPAINTING3D_BUILD_INSTALL_ROOT}"
    rm -rf remesh_isotropic_planar
    git clone https://github.com/toshas/remesh_isotropic_planar.git
    cd remesh_isotropic_planar
    git checkout ${REMESH_VERSION}
    cmake -B build \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_PREFIX_PATH="${REPAINTING3D_INSTALL_PREFIX}" \
        -DCMAKE_INSTALL_PREFIX="${REPAINTING3D_INSTALL_PREFIX}"
    cmake --build build --target install -j
    touch "${REPAINTING3D_INSTALL_PREFIX}/.marker.dep6.remesher.installed"
fi

if [ ! -f "${REPAINTING3D_INSTALL_PREFIX}/.marker.dep7.draco.installed" ]; then
    cd "${REPAINTING3D_BUILD_INSTALL_ROOT}"
    wget -O draco-${DRACO_VERSION}.tar.gz https://github.com/google/draco/archive/refs/tags/${DRACO_VERSION}.tar.gz
    tar -xf draco-${DRACO_VERSION}.tar.gz
    cd draco-${DRACO_VERSION}
    mkdir -p build
    cd build
    cmake \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_PREFIX_PATH="${REPAINTING3D_INSTALL_PREFIX}" \
        -DCMAKE_INSTALL_PREFIX="${REPAINTING3D_INSTALL_PREFIX}" \
        ..
    make install
    touch "${REPAINTING3D_INSTALL_PREFIX}/.marker.dep7.draco.installed"
fi

cleanup() {
    rm "${REPAINTING3D_BUILD_INSTALL_ROOT}/boost_${BOOST_VERSION_UNDERSCORE}.tar.gz"
    rm -rf "${REPAINTING3D_BUILD_INSTALL_ROOT}/boost_${BOOST_VERSION_UNDERSCORE}"

    rm "${REPAINTING3D_BUILD_INSTALL_ROOT}/gmp-${GMP_VERSION}.tar.xz"
    rm -rf "${REPAINTING3D_BUILD_INSTALL_ROOT}/gmp-${GMP_VERSION}"

    rm "${REPAINTING3D_BUILD_INSTALL_ROOT}/mpfr-${MPFR_VERSION}.tar.xz"
    rm -rf "${REPAINTING3D_BUILD_INSTALL_ROOT}/mpfr-${MPFR_VERSION}"

    rm "${REPAINTING3D_BUILD_INSTALL_ROOT}/eigen-${EIGEN_VERSION}.tar.gz"
    rm -rf "${REPAINTING3D_BUILD_INSTALL_ROOT}/eigen-${EIGEN_VERSION}"

    rm "${REPAINTING3D_BUILD_INSTALL_ROOT}/CGAL-${CGAL_VERSION}-library.tar.xz"
    rm -rf "${REPAINTING3D_BUILD_INSTALL_ROOT}/CGAL-${CGAL_VERSION}"

    rm -rf "${REPAINTING3D_BUILD_INSTALL_ROOT}/remesh_isotropic_planar"

    rm "${REPAINTING3D_BUILD_INSTALL_ROOT}/draco-${DRACO_VERSION}.tar.gz"
    rm -rf "${REPAINTING3D_BUILD_INSTALL_ROOT}/draco-${DRACO_VERSION}"

    rm -rf "${REPAINTING3D_INSTALL_PREFIX}/include"
    rm -rf "${REPAINTING3D_INSTALL_PREFIX}/share"
    rm -rf "${REPAINTING3D_INSTALL_PREFIX}/lib/cmake"
    rm -rf "${REPAINTING3D_INSTALL_PREFIX}/lib/pkgconfig"
    rm "${REPAINTING3D_INSTALL_PREFIX}/lib/*.a"
}
