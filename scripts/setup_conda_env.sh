#!/usr/bin/env bash
set -e
set -x

if ! type shopt > /dev/null 2>&1; then
    echo "This script requires bash interpreter"
    exit 255
fi

SL3A_ENV_NAME=${SL3A_ENV_NAME:-sl3a}

SELF=$(realpath "$0")
SELF_DIR=$(dirname "${SELF}")
SL3A_CODE_ROOT=$(realpath "${SELF_DIR}/..")

if [ ! -f "${SL3A_CONDA_ROOT}/miniconda3/bin/conda" ]; then
    echo "\"conda\" not found, check setup_conda_bin.sh"
    exit 255
fi

"${SL3A_CONDA_ROOT}/miniconda3/bin/conda" create -y -n ${SL3A_ENV_NAME} python=3.9

# conda activate ${SL3A_ENV_NAME}
source "${SL3A_CONDA_ROOT}/miniconda3/bin/activate" ${SL3A_ENV_NAME}

conda install -y pytorch=1.13.0 torchvision pytorch-cuda=11.6 -c pytorch -c nvidia
conda install -y -c fvcore -c iopath -c conda-forge fvcore iopath ffmpeg
conda install -y pytorch3d -c pytorch3d
pip install -r "${SL3A_CODE_ROOT}/requirements.txt"
echo "Conda environment \"${SL3A_ENV_NAME}\" is now installed"
