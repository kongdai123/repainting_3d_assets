#!/usr/bin/env bash
set -e
set -x

SL3A_CONDA_INSTALLER_FILE="${SL3A_CONDA_INSTALLER_FILE:-Miniconda3-py38_23.3.1-0-Linux-x86_64.sh}"

if [ -z "${SL3A_CONDA_ROOT}" ]; then
    echo "SL3A_CONDA_ROOT not set or is empty"
    exit 255
fi

if [ -f "${SL3A_CONDA_ROOT}/.marker.conda.completed" ]; then
    echo "Conda already installed"
    exit 0
fi

if [ -d "${SL3A_CONDA_ROOT}" ]; then
    echo "${SL3A_CONDA_ROOT} is an existing directory"
    exit 255
fi

mkdir -p "${SL3A_CONDA_ROOT}"
cd "${SL3A_CONDA_ROOT}"
wget https://repo.anaconda.com/miniconda/${SL3A_CONDA_INSTALLER_FILE}
bash ${SL3A_CONDA_INSTALLER_FILE} -b -p "${SL3A_CONDA_ROOT}/miniconda3"
touch "${SL3A_CONDA_ROOT}/.marker.conda.completed"
