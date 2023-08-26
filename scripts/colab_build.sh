#!/usr/bin/env bash
set -e
if [ ! -z "${DEBUG}" ]; then
    set -x
fi

HAVE_CUDA=$(python -c 'import torch; print(torch.cuda.is_available())')
if [ "${HAVE_CUDA}" = False ]; then
    echo "CUDA not found, change the runtime to proceed!"
    exit 255
fi

export REPAINTING3D_INSTANTNGP_ARCHS=$(python -c 'import torch; props=torch.cuda.get_device_properties(0); print(f"{props.major}{props.minor}")')
export WORK_ROOT=./repainting_root

# Download and install conda
if [ ! -f done.conda.txt ]; then
    scripts/setup.sh "${WORK_ROOT}"
    pip3 install --upgrade pip
    pip3 install trimesh  # local visualization in the notebook
    touch done.conda.txt
fi
