#!/usr/bin/env bash
set -e
set -x

if [ -z "${SL3A_DATASET_ROOT}" ]; then
    echo "SL3A_DATASET_ROOT not set or is empty"
    exit 255
fi

if [ -f "${SL3A_ROOT}/.marker.dataset.completed" ]; then
    echo "Dataset already prepared"
    exit 0
fi

if [ -d "${SL3A_DATASET_ROOT}" ]; then
    echo "${SL3A_DATASET_ROOT} is an existing directory, aborting"
    exit 255
fi

mkdir -p "${SL3A_DATASET_ROOT}"
cd "${SL3A_DATASET_ROOT}"

wget https://shapenet.cs.stanford.edu/shapenet/obj-zip/ShapeNetSem.v0/models-OBJ.zip --no-check-certificate
wget https://shapenet.cs.stanford.edu/shapenet/obj-zip/ShapeNetSem.v0/metadata.csv --no-check-certificate

unzip models-OBJ.zip

touch "${SL3A_ROOT}/.marker.dataset.completed"
